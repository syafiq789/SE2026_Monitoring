import io
from pathlib import Path
from types import SimpleNamespace
import pandas as pd
import pytest
from app import create_app
from config import Config
from extensions import db
from models.user import User
from models.monitoring import SLS
from services.upload_service import prepare_import_data, import_prepared_data
from utils.validators import ImportValidationError
ROOT = None

@pytest.fixture(autouse=True)
def workspace(tmp_path):
    global ROOT
    ROOT = tmp_path
    for name in ('fixtures', 'uploads', 'exports'):
        (ROOT / name).mkdir(parents=True, exist_ok=True)

def row(**overrides):
    r = dict(prov='35', kab='10', kec_code='010', kec_name='Kecamatan A', desa_code='001', desa_name='Desa A', subsls_code='000100', subsls_name='SLS A', PCL='Petugas A', PML='Pengawas A', total='100', OPEN='20', DRAFT='10')
    r.update(overrides)
    return r

def prepare(rows):
    p = ROOT / 'fixtures/data.csv'
    pd.DataFrame(rows).to_csv(p, index=False)
    return prepare_import_data(p)

@pytest.fixture
def app(workspace):

    class Cfg(Config):
        TESTING = True
        SECRET_KEY = 'audit-dummy-only'
        SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
        SQLALCHEMY_ENGINE_OPTIONS = {}
        ALLOW_PUBLIC_REGISTER = False
        UPLOAD_FOLDER = str(ROOT / 'uploads')
        EXPORT_FOLDER = str(ROOT / 'exports')
    a = create_app(Cfg)
    with a.app_context():
        db.create_all()
        u = User(nama_lengkap='Dummy Admin', username='fixture_admin', email='admin@audit.invalid', role='admin', is_active=True)
        u.set_password('dummy-pass-123')
        db.session.add(u)
        v = User(nama_lengkap='Dummy User', username='fixture_user', email='user@audit.invalid', role='user', is_active=True)
        v.set_password('dummy-pass-123')
        db.session.add(v)
        db.session.commit()
    yield a
    with a.app_context():
        db.session.remove()
        db.drop_all()

def login(c, name='fixture_admin'):
    return c.post('/login', data=dict(username=name, password='dummy-pass-123'))

def test_public_registration_respects_disabled_flag(app):
    c = app.test_client()
    c.post('/register', data=dict(nama_lengkap='New', username='new', email='new@audit.invalid', role='admin', password='dummy-pass-123', confirm_password='dummy-pass-123'))
    with app.app_context():
        assert User.query.filter_by(username='new').first() is None, 'Registration still creates user with flag False'

def test_anonymous_cannot_self_assign_admin(app):
    app.config['ALLOW_PUBLIC_REGISTER'] = True
    c = app.test_client()
    c.post('/register', data=dict(nama_lengkap='New', username='new', email='new@audit.invalid', role='admin', password='dummy-pass-123', confirm_password='dummy-pass-123'))
    login_result = c.post('/login', data=dict(username='new', password='dummy-pass-123'))
    assert c.get('/admin/users').status_code != 200, 'Public registration obtains admin access'

def test_real_role_denies_user_upload_export_users(app):
    c = app.test_client()
    login(c, 'fixture_user')
    for path in ['/upload', '/export/sls/csv', '/admin/users']:
        assert c.get(path).status_code == 403
    for path in ['/dashboard', '/monitoring-sls', '/api/dashboard-data']:
        assert c.get(path).status_code == 200

def test_inactive_user_session_revoked(app):
    c = app.test_client()
    login(c)
    with app.app_context():
        u = User.query.filter_by(username='fixture_admin').one()
        u.is_active = False
        db.session.commit()
    assert c.get('/admin/users').status_code == 302

def test_deleted_user_does_not_resurrect(app):
    c = app.test_client()
    login(c)
    with app.app_context():
        u = User.query.filter_by(username='fixture_admin').one()
        db.session.delete(u)
        db.session.commit()
    assert c.get('/admin/users').status_code != 200, 'Deleted principal restored from cookie'

def test_empty_normalized_input_rejected_before_replacement(app):
    with app.app_context():
        import_prepared_data(prepare([row()]))
        db.session.commit()
        try:
            prepared = prepare([{k: ' ' for k in row()}])
        except ImportValidationError:
            return
        import_prepared_data(prepared)
        db.session.commit()
        assert SLS.query.count() == 1, 'Whitespace CSV committed zero rows and erased snapshot'

def test_header_only_is_rejected():
    p = ROOT / 'fixtures/empty.csv'
    p.write_text(','.join(row()) + '\n')
    with pytest.raises(ImportValidationError):
        prepare_import_data(p)

def test_assignment_change_does_not_double_same_sls():
    with pytest.raises(ImportValidationError):
        prepare([row(), row(PCL='Other PCL')])

@pytest.mark.parametrize('value', ['abc', '-1', '0.5'])
def test_invalid_counts_rejected(value):
    with pytest.raises(ImportValidationError):
        prepare([row(OPEN=value, DRAFT='0')])

def test_invalid_count_does_not_claim_full_completion():
    try:
        p = prepare([row(OPEN='abc', DRAFT='0')])
    except ImportValidationError:
        return
    assert p['records'][0]['progress'] != 100, 'Invalid OPEN coerced zero, progress=100%'

def test_identical_duplicate_skipped():
    p = prepare([row(), row()])
    assert len(p['records']) == 1 and p['duplicate_rows'] == 1

def test_conflict_same_assignment_rejected():
    with pytest.raises(ImportValidationError):
        prepare([row(), row(total='101')])

def test_valid_import_dashboard_and_csv_export(app, monkeypatch):
    import services.export_service as es
    monkeypatch.setattr(es, 'export_timestamp', lambda: 'AUDIT')
    with app.app_context():
        import_prepared_data(prepare([row()]))
        db.session.commit()
    c = app.test_client()
    login(c)
    for path in ['/dashboard', '/monitoring-sls', '/monitoring-pcl', '/monitoring-pml', '/monitoring-kecamatan', '/peta-spasial', '/api/dashboard-data', '/api/chart-data', '/api/filter-data']:
        r = c.get(path)
        assert r.status_code == 200, (path, r.status_code)
    r = c.get('/export/sls/csv')
    assert r.status_code == 200
    assert b'SLS A' in r.data
    r = c.get('/api/monitoring/sls-dt?draw=1&start=0&length=10')
    assert r.status_code == 200
    assert len(r.json['data']) == 1
    assert r.json['data'][0]['processed_count'] == 70

def test_failed_upload_preserves_existing_data(app, monkeypatch):
    import routes.upload_routes as ur
    monkeypatch.setattr(ur, 'uuid4', lambda: SimpleNamespace(hex='AUDIT'))
    with app.app_context():
        import_prepared_data(prepare([row()]))
        db.session.commit()
    c = app.test_client()
    login(c)
    data = pd.DataFrame([row(), row(total='101')]).to_csv(index=False).encode()
    r = c.post('/upload-data', data={'file': (io.BytesIO(data), 'sls.csv')}, content_type='multipart/form-data')
    assert r.status_code in (200, 302)
    with app.app_context():
        assert SLS.query.count() == 1 and SLS.query.first().total_target == 100

def test_excel_export_names_remain_text(app, monkeypatch):
    import services.export_service as es
    from openpyxl import load_workbook
    monkeypatch.setattr(es, 'export_timestamp', lambda: 'AUDIT')
    with app.app_context():
        import_prepared_data(prepare([row(PCL='=1+1')]))
        db.session.commit()
        p = es.create_export('sls', 'excel', {})
        book = load_workbook(p, data_only=False)
        sheet = book.active
        headers = {c.value: c.column for c in sheet[4]}
        cell = sheet.cell(5, headers['Nama PCL'])
        assert cell.data_type != 'f', 'Name emitted as executable formula, not text'

def test_filtered_exports_have_distinct_artifacts(app, monkeypatch):
    import services.export_service as es
    monkeypatch.setattr(es, 'export_timestamp', lambda: 'AUDIT')
    with app.app_context():
        import_prepared_data(prepare([row(), row(kec_code='020', subsls_code='000200', PCL='Other')]))
        db.session.commit()
        a = es.create_export('sls', 'csv', {'kec_code': '010'})
        original = a.read_bytes()
        b = es.create_export('sls', 'csv', {'kec_code': '020'})
        assert a != b and a.read_bytes() == original, 'Same-second filtered export overwrote previous artifact'

def test_whitespace_upload_route_preserves_snapshot(app, monkeypatch):
    import routes.upload_routes as ur
    monkeypatch.setattr(ur, 'uuid4', lambda: SimpleNamespace(hex='AUDIT'))
    with app.app_context():
        import_prepared_data(prepare([row()]))
        db.session.commit()
    c = app.test_client()
    login(c)
    data = pd.DataFrame([{k: ' ' for k in row()}]).to_csv(index=False).encode()
    r = c.post('/upload-data', data={'file': (io.BytesIO(data), 'sls.csv')}, content_type='multipart/form-data')
    assert r.status_code in (200, 302)
    with app.app_context():
        assert SLS.query.count() == 1, 'HTTP upload accepted whitespace CSV and removed old SLS'

def test_import_database_failure_rolls_back_snapshot(app, monkeypatch):
    import routes.upload_routes as ur
    from sqlalchemy.exc import IntegrityError
    monkeypatch.setattr(ur, 'uuid4', lambda: SimpleNamespace(hex='AUDIT'))
    with app.app_context():
        import_prepared_data(prepare([row()]))
        db.session.commit()
    real = ur.import_prepared_data

    def fail(prepared):
        real(prepared)
        raise IntegrityError('audit injected persistence failure', {}, None)
    monkeypatch.setattr(ur, 'import_prepared_data', fail)
    c = app.test_client()
    login(c)
    data = pd.DataFrame([row(total='200')]).to_csv(index=False).encode()
    r = c.post('/upload-data', data={'file': (io.BytesIO(data), 'sls.csv')}, content_type='multipart/form-data')
    assert r.status_code in (200, 302)
    with app.app_context():
        assert SLS.query.count() == 1 and SLS.query.first().total_target == 100

def test_weighted_aggregation_and_export_filter(app, monkeypatch):
    from services.monitoring_service import dashboard_summary, get_sls_rows
    with app.app_context():
        import_prepared_data(prepare([row(total='100', OPEN='50', DRAFT='0'), row(kec_code='020', subsls_code='000200', total='900', OPEN='0', DRAFT='0')]))
        db.session.commit()
        rows = get_sls_rows({'kec_code': '010'})
        assert len(rows) == 1 and rows[0]['total_target'] == 100
        summary = dashboard_summary()
        assert summary['progress'] == 95, summary

def test_duplicate_assignment_does_not_double_dashboard(app):
    from services.monitoring_service import dashboard_summary
    with app.app_context():
        import_prepared_data(prepare([row()]))
        db.session.commit()
        with pytest.raises(ImportValidationError):
            prepare([row(), row(PCL='Other PCL')])
        summary = dashboard_summary()
        assert summary['total_target'] == 100 and summary['total_sls'] == 1, summary

def test_documented_bearer_api_exists(app):
    routes = {r.rule for r in app.url_map.iter_rules()}
    assert {'/api/v1/dashboard', '/api/v1/monitoring/sls'} <= routes, 'README API routes not implemented'

def test_jinja_templates_compile(app):
    for name in app.jinja_env.list_templates():
        app.jinja_env.get_template(name)

@pytest.mark.parametrize('total,op,draft', [(0, 0, 0), (1, 0, 0), (100, 101, 0), (100, 25, 25), (10, 0, 15)])
def test_progress_invariants(total, op, draft):
    from utils.calculations import calculate_progress
    result = calculate_progress(total, op, draft)
    assert result.processed == min(max(total - op - draft, 0), total)
    assert result.processed + result.remaining == total
    assert 0 <= result.progress <= 100

@pytest.mark.parametrize('key', ['', 'se2026-bps-banyuwangi-secret-key-local', 'se2026-bps-banyuwangi-secret'])
def test_missing_or_public_signing_key_rejected(key):

    class Cfg(Config):
        SECRET_KEY = key
    with pytest.raises(RuntimeError, match='SECRET_KEY'):
        create_app(Cfg)

def test_vercel_requires_persistent_database(monkeypatch):

    class Cfg(Config):
        IS_VERCEL = True
        SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    monkeypatch.delenv('DATABASE_URL', raising=False)
    with pytest.raises(RuntimeError, match='persistent'):
        create_app(Cfg)

def test_legacy_registration_snapshot_cannot_restore_admin(app):
    c = app.test_client()
    with c.session_transaction() as state:
        state['registered_snapshots'] = [dict(username='ghost', email='ghost@audit.invalid', role='admin', is_active=True)]
    assert c.get('/admin/users').status_code == 302
    with app.app_context():
        assert User.query.filter_by(username='ghost').first() is None

def test_session_does_not_contain_password_snapshot(app):
    c = app.test_client()
    login(c)
    with c.session_transaction() as state:
        assert 'user_id' in state
        assert 'user_snapshot' not in state and 'registered_snapshots' not in state

def test_empty_import_guard_preserves_data(app):
    with app.app_context():
        import_prepared_data(prepare([row()]))
        db.session.commit()
        with pytest.raises(ImportValidationError):
            import_prepared_data({'records': []})
        assert SLS.query.count() == 1

@pytest.mark.parametrize('value', ['NaN', 'Infinity', '2147483648', ''])
def test_nonfinite_overflow_and_missing_counts_rejected(value):
    with pytest.raises(ImportValidationError):
        prepare([row(OPEN=value)])

def test_bearer_api_requires_active_admin_token(app):
    from services.token_service import create_api_token
    from models.api_token import ApiToken
    with app.app_context():
        import_prepared_data(prepare([row()]))
        db.session.commit()
        admin = User.query.filter_by(username='fixture_admin').one()
        token, raw = create_api_token(admin.id, 'fixture', 1)
        token_id = token.id
    c = app.test_client()
    headers = {'Authorization': 'Bearer ' + raw}
    assert c.get('/api/v1/dashboard').status_code == 401
    assert c.get('/api/v1/dashboard', headers={'Authorization': 'Bearer invalid'}).status_code == 401
    assert c.get('/api/v1/dashboard', headers=headers).status_code == 200
    result = c.get('/api/v1/monitoring/sls?per_page=9999&kec_code=010', headers=headers)
    assert result.status_code == 200 and result.json['per_page'] == 1000 and (result.json['total'] == 1)
    with app.app_context():
        token = db.session.get(ApiToken, token_id)
        token.is_active = False
        db.session.commit()
    assert c.get('/api/v1/dashboard', headers=headers).status_code == 401

def test_bearer_revoked_on_disabled_or_demoted_owner(app):
    from services.token_service import create_api_token
    with app.app_context():
        admin = User.query.filter_by(username='fixture_admin').one()
        _, raw = create_api_token(admin.id, 'fixture', 1)
    c = app.test_client()
    headers = {'Authorization': 'Bearer ' + raw}
    with app.app_context():
        admin = User.query.filter_by(username='fixture_admin').one()
        admin.is_active = False
        db.session.commit()
    assert c.get('/api/v1/dashboard', headers=headers).status_code == 401
    with app.app_context():
        admin = User.query.filter_by(username='fixture_admin').one()
        admin.is_active = True
        admin.role = 'user'
        db.session.commit()
    assert c.get('/api/v1/dashboard', headers=headers).status_code == 401

def test_bearer_expiry_and_token_menu(app):
    from datetime import datetime, timedelta
    from models.api_token import ApiToken
    from services.token_service import create_api_token
    with app.app_context():
        admin = User.query.filter_by(username='fixture_admin').one()
        token, raw = create_api_token(admin.id, 'expired', 1)
        token.expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.session.commit()
    c = app.test_client()
    assert c.get('/api/v1/dashboard', headers={'Authorization': 'Bearer ' + raw}).status_code == 401
    login(c, 'fixture_user')
    assert c.get('/admin/api-tokens').status_code == 403
    login(c)
    r = c.post('/admin/api-tokens', data={'name': 'New token', 'expires_days': '1'})
    assert r.status_code == 200 and r.headers['Cache-Control'] == 'no-store'
    assert b'se2026_' in r.data
    with app.app_context():
        token = ApiToken.query.filter_by(name='New token').one()
        token_id = token.id
        assert 'se2026_' not in token.token_hash
    assert c.post(f'/admin/api-tokens/{token_id}/revoke').status_code == 302
    with app.app_context():
        assert not db.session.get(ApiToken, token_id).is_active

def test_datatable_limits_negative_and_zero_length(app):
    with app.app_context():
        import_prepared_data(prepare([row(), row(subsls_code='000200')]))
        db.session.commit()
    c = app.test_client()
    login(c)
    for length in ['0', '-1']:
        r = c.get('/api/monitoring/sls-dt?start=-1&length=' + length)
        assert r.status_code == 200 and len(r.json['data']) == 1

def test_csv_formula_neutralization(app, monkeypatch):
    import services.export_service as es
    with app.app_context():
        import_prepared_data(prepare([row(PCL='=1+1')]))
        db.session.commit()
        p = es.create_export('sls', 'csv', {})
        assert "'=1+1" in p.read_text(encoding='utf-8-sig')

def test_no_default_accounts_created_on_request(app):
    c = app.test_client()
    c.get('/login')
    with app.app_context():
        assert User.query.filter_by(username='admin').first() is None

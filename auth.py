from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    session,
    request,
    current_app,
)
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from forms import LoginForm, ResetRequestForm
from models import User, db
from sqlalchemy import func

auth_bp = Blueprint('auth', __name__)


def _serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])


def generate_reset_token(user):
    s = _serializer()
    return s.dumps({'user_id': user.id, 'pw': user.password})


def verify_reset_token(token, max_age=3600):
    s = _serializer()
    try:
        data = s.loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
    user = db.session.get(User, data.get('user_id'))
    if not user or user.password != data.get('pw'):
        return None
    return user


@auth_bp.route('/reset', methods=['GET', 'POST'])
@auth_bp.route('/recovery-request', methods=['GET', 'POST'])
def reset_request():
    form = ResetRequestForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        if user:
            token = generate_reset_token(user)
            reset_url = url_for('auth.recovery_password', token=token, _external=True)
            from app import send_email
            html = render_template('emails/password_reset.html', reset_url=reset_url)
            send_email(
                email,
                '[Tiendix] - recuperacion de contraseña',
                html,
                asynchronous=False,
            )
        flash('Si el correo existe, se enviará un enlace de restablecimiento', 'login')
        return redirect(url_for('auth.login'))
    return render_template('reset_request.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = (getattr(getattr(form, 'username', None), 'data', None) or request.form.get('username') or '').strip().lower()
        password = getattr(getattr(form, 'password', None), 'data', None) or request.form.get('password')
        user = User.query.filter(func.lower(User.username) == username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['role'] = user.role
            session['company_id'] = user.company_id
            session['username'] = user.username
            session['full_name'] = f"{user.first_name} {user.last_name}".strip()
            from app import log_audit
            log_audit('login_success', 'auth', user.id, details=f'username={user.username}')
            return redirect(url_for('index'))
        from app import log_audit
        log_audit('login_failed', 'auth', status='fail', details=f'username={username or ""}')
        flash('Credenciales inválidas', 'login')
    return render_template('login.html', form=form, company=None)

@auth_bp.route('/logout')
def logout():
    from app import log_audit
    log_audit('logout', 'auth')
    session.clear()
    return redirect(url_for('auth.login'))


@auth_bp.route('/reset/<token>', methods=['GET', 'POST'], endpoint='reset_password')
@auth_bp.route('/recovery/<token>', methods=['GET', 'POST'], endpoint='recovery_password')
def reset_password(token):
    user = verify_reset_token(token)
    if not user:
        flash('Token inválido o expirado', 'login')
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        password = request.form.get('password')
        if not password:
            flash('Contraseña requerida', 'login')
            return render_template('reset_password.html', token=token)
        if len(password) < 6:
            flash('La contraseña debe tener mínimo 6 caracteres', 'login')
            return render_template('reset_password.html', token=token)
        user.set_password(password)
        db.session.commit()
        flash('Contraseña actualizada', 'login')
        return redirect(url_for('auth.login'))
    return render_template('reset_password.html', token=token)

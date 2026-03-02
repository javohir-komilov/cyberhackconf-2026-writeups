/* VaultPass — Main JavaScript */

'use strict';

/* ---- Toggle password visibility ---- */
function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const eye   = document.getElementById(inputId + '-eye');
    if (!input) return;
    if (input.type === 'password') {
        input.type = 'text';
        if (eye) eye.className = 'bi bi-eye-slash';
    } else {
        input.type = 'password';
        if (eye) eye.className = 'bi bi-eye';
    }
}

/* ---- Reveal/mask vault entry password ---- */
function toggleReveal(spanId) {
    const span = document.getElementById(spanId);
    const eye  = document.getElementById('eye-' + spanId.replace('pass-', ''));
    if (!span) return;
    if (span.classList.contains('vp-masked')) {
        span.classList.remove('vp-masked');
        span.textContent = span.dataset.real || '(empty)';
        if (eye) eye.className = 'bi bi-eye-slash';
    } else {
        span.classList.add('vp-masked');
        span.textContent = '••••••••';
        if (eye) eye.className = 'bi bi-eye';
    }
}

/* ---- Password strength indicator ---- */
(function () {
    const passInput = document.getElementById('password');
    const bar = document.getElementById('strength-bar');
    if (!passInput || !bar) return;

    passInput.addEventListener('input', function () {
        const v = passInput.value;
        let score = 0;
        if (v.length >= 8)  score++;
        if (v.length >= 12) score++;
        if (/[A-Z]/.test(v)) score++;
        if (/[0-9]/.test(v)) score++;
        if (/[^A-Za-z0-9]/.test(v)) score++;

        const labels = ['', 'Very Weak', 'Weak', 'Fair', 'Strong', 'Very Strong'];
        const colors = ['', '#ef4444', '#f59e0b', '#eab308', '#10b981', '#3b82f6'];
        const pct    = score * 20;

        bar.innerHTML = `
            <div style="height:4px; background:#334155; border-radius:2px; overflow:hidden; margin-top:4px;">
                <div style="width:${pct}%; height:100%; background:${colors[score] || '#334155'};
                     border-radius:2px; transition:width .25s,background .25s;"></div>
            </div>
            <span style="font-size:.72rem; color:${colors[score] || '#94a3b8'}; margin-top:2px; display:block;">
                ${labels[score] || ''}
            </span>`;
    });
}());

/* ---- Vault search filter ---- */
(function () {
    const searchInput = document.getElementById('vaultSearch');
    if (!searchInput) return;
    searchInput.addEventListener('input', function () {
        const q = this.value.toLowerCase();
        document.querySelectorAll('.vp-entry-card').forEach(card => {
            const text = card.textContent.toLowerCase();
            card.closest('.col-xl-4, .col-lg-6').style.display =
                q === '' || text.includes(q) ? '' : 'none';
        });
    });
}());

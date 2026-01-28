// Carpintaria Digital - JavaScript Global

// Inicialização quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    // Animações de entrada
    initAnimations();
    
    // Formulários
    initForms();
    
    // Navegação suave
    initSmoothScroll();
    
    // Botões WhatsApp
    initWhatsAppButtons();
});

// Animações de entrada
function initAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in-up');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observar elementos para animação
    document.querySelectorAll('.card, .secao-sobre, .secao-plataformas').forEach(el => {
        observer.observe(el);
    });
}

// Inicializar formulários
function initForms() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Validação básica
            const inputs = form.querySelectorAll('input[required], textarea[required]');
            let isValid = true;
            
            inputs.forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    input.classList.add('is-invalid');
                } else {
                    input.classList.remove('is-invalid');
                }
            });
            
            if (isValid) {
                // Simular envio
                showSuccessMessage('Mensagem enviada com sucesso! Entraremos em contacto em breve.');
                form.reset();
            } else {
                showErrorMessage('Por favor, preencha todos os campos obrigatórios.');
            }
        });
    });
}

// Navegação suave
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Botões WhatsApp
function initWhatsAppButtons() {
    document.querySelectorAll('.btn-whatsapp').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const numero = this.dataset.numero || '258840000000';
            const mensagem = this.dataset.mensagem || 'Olá! Gostaria de saber mais sobre os serviços da Carpintaria Digital.';
            const url = `https://wa.me/${numero}?text=${encodeURIComponent(mensagem)}`;
            window.open(url, '_blank');
        });
    });
}

// Mostrar mensagem de sucesso
function showSuccessMessage(message) {
    showToast(message, 'success');
}

// Mostrar mensagem de erro
function showErrorMessage(message) {
    showToast(message, 'error');
}

// Sistema de toast/notificações
function showToast(message, type = 'info') {
    // Remover toast existente
    const existingToast = document.querySelector('.toast-notification');
    if (existingToast) {
        existingToast.remove();
    }
    
    // Criar novo toast
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <span class="toast-message">${message}</span>
            <button class="toast-close" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
    `;
    
    // Adicionar estilos inline
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 9999;
        max-width: 400px;
        animation: slideInRight 0.3s ease-out;
    `;
    
    document.body.appendChild(toast);
    
    // Remover automaticamente após 5 segundos
    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => toast.remove(), 300);
        }
    }, 5000);
}

// Adicionar estilos de animação para toast
const toastStyles = document.createElement('style');
toastStyles.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .toast-content {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .toast-close {
        background: none;
        border: none;
        color: white;
        font-size: 20px;
        cursor: pointer;
        margin-left: 15px;
        padding: 0;
        line-height: 1;
    }
    
    .toast-close:hover {
        opacity: 0.8;
    }
`;
document.head.appendChild(toastStyles);

// Utilitários
function formatPhoneNumber(phone) {
    // Remover caracteres não numéricos
    const cleaned = phone.replace(/\D/g, '');
    
    // Adicionar código do país se necessário (Moçambique: +258)
    if (cleaned.length === 9 && cleaned.startsWith('8')) {
        return '258' + cleaned;
    }
    
    return cleaned;
}

// Validação de email
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Máscara para telefone
function phoneMask(input) {
    let value = input.value.replace(/\D/g, '');
    
    if (value.length <= 9) {
        value = value.replace(/(\d{2})(\d{3})(\d{4})/, '$1 $2 $3');
    }
    
    input.value = value;
}


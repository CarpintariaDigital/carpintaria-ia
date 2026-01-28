// CHATBOT SOBERANO - LÓGICA
const chatData = {
    start: {
        msg: "Olá! 👋 Bem-vindo à Carpintaria Digital. Eu sou o Assistente Virtual. Como posso ajudar o seu negócio hoje?",
        options: [
            { text: "🚀 Ver Plataformas", next: "platforms" },
            { text: "💰 Consultoria", next: "consulting" },
            { text: "📞 Falar com Humano", next: "contact" }
        ]
    },
    platforms: {
        msg: "Temos soluções incríveis! Qual lhe interessa?",
        options: [
            { text: "TiConta (ERP)", action: "link", url: "https://app.carpintariadigital.com" },
            { text: "Txiling (Eventos)", action: "goto", url: "Txiling.html" },
            { text: "Voltar", next: "start" }
        ]
    },
    consulting: {
        msg: "Ótima escolha. Ajudamos empresas a digitalizar processos. Gostaria de agendar um diagnóstico gratuito?",
        options: [
            { text: "Sim, no WhatsApp", action: "whatsapp", text: "Olá! Quero um diagnóstico para a minha empresa." },
            { text: "Não, obrigado", next: "start" }
        ]
    },
    contact: {
        msg: "Sem problema. Pode ligar ou mandar mensagem direta.",
        options: [
            { text: "WhatsApp Direto", action: "whatsapp", text: "Olá Ildino, preciso de falar consigo." },
            { text: "Voltar", next: "start" }
        ]
    }
};

// Elementos
const chatWindow = document.getElementById('chatWindow');
const messagesArea = document.getElementById('chatMessages');

function toggleChat() {
    chatWindow.classList.toggle('active');
    if (chatWindow.classList.contains('active') && messagesArea.children.length === 0) {
        showNode('start');
    }
}

function showNode(nodeName) {
    const data = chatData[nodeName];
    addMessage(data.msg, 'bot');
    
    // Remover opções antigas
    const oldOptions = document.querySelectorAll('.chat-options');
    oldOptions.forEach(el => el.remove());

    // Criar novas opções
    if (data.options) {
        const optionsDiv = document.createElement('div');
        optionsDiv.className = 'chat-options';
        
        data.options.forEach(opt => {
            const btn = document.createElement('button');
            btn.className = 'option-btn';
            btn.innerText = opt.text;
            btn.onclick = () => handleOption(opt);
            optionsDiv.appendChild(btn);
        });
        
        messagesArea.appendChild(optionsDiv);
        scrollToBottom();
    }
}

function handleOption(opt) {
    // Adicionar escolha do usuário como mensagem
    addMessage(opt.text, 'user');

    if (opt.next) {
        setTimeout(() => showNode(opt.next), 500);
    } else if (opt.action === 'link') {
        window.open(opt.url, '_blank');
        addMessage("Abri o link numa nova aba! 😊", 'bot');
    } else if (opt.action === 'goto') {
        window.location.href = opt.url;
    } else if (opt.action === 'whatsapp') {
        window.open(`https://wa.me/258840000000?text=${encodeURIComponent(opt.text)}`, '_blank');
        addMessage("Redirecionando para o WhatsApp...", 'bot');
    }
}

function addMessage(text, sender) {
    const div = document.createElement('div');
    div.className = `msg msg-${sender}`;
    div.innerText = text;
    messagesArea.appendChild(div);
    scrollToBottom();
}

function scrollToBottom() {
    messagesArea.scrollTop = messagesArea.scrollHeight;
}

// Enter para enviar (simulação simples)
function handleInput(e) {
    if (e.key === 'Enter') {
        const input = document.getElementById('user-input');
        if (input.value.trim()) {
            addMessage(input.value, 'user');
            input.value = '';
            setTimeout(() => addMessage("Ainda estou a aprender a ler texto livre! Por favor, use os botões acima. 😅", 'bot'), 1000);
        }
    }
}

# 📊 Estado da União: Carpintaria OS 2026

**Data:** 27 de Janeiro de 2026
**Versão do Sistema:** 3.0 (FastAPI Core + PWA Modules)

---

## 🚀 Onde Estamos (Visão Geral)

Concluímos com sucesso a **Grande Migração** da arquitetura monolítica (Streamlit) para um ecossistema moderno, modular e "Cloud-Native" mas "Offline-First".

O **Carpintaria OS** agora é composto por:
1.  **Cérebro Central (`ia_core`)**: Um backend FastAPI robusto que serve tanto como API para os agentes quanto como servidor de arquivos estáticos.
2.  **Módulos PWA (`static/platforms`)**: Txiling, Academia, Market e Saúde agora são Progressive Web Apps independentes. Podem ser instalados em telemóveis e PCs, funcionando offline.
3.  **Interface Híbrida**: O `Escritorio.html` (Gestão Humana) coexiste com a API dos Agentes IA.

---

## 🛠️ O Que Foi Feito (e Porquê)

### Fase 1: Fundação FastAPI
*   **Ação:** Criámos `main.py` substituindo o antigo `interface_carpintaria.py`.
*   **Porquê:** O Streamlit era pesado e difícil de integrar com interfaces web customizadas. FastAPI permite criar APIs rápidas e servir qualquer frontend (HTML/JS/React) com zero overhead.

### Fase 2: PWA Revolution (Txiling, Academia, etc.)
*   **Ação:** Movemos as pastas de `platforms/` para `static/platforms/` e adicionámos `manifest.json` e `sw.js` em cada uma.
*   **Porquê:** Para cumprir a visão de "Offline-First". Agora, um cliente pode acessar o Txiling uma vez, instalar no celular e usar mesmo sem internet (graças ao Service Worker).

### Fase 3: Deployment Vercel
*   **Ação:** Configurámos `vercel.json` e `api/index.py`.
*   **Porquê:** Permite hospedar todo o sistema no plano **Hobby (Grátis)** da Vercel. A API roda como Serverless Functions e os HTMLs são servidos via CDN global. Zero custo de infraestrutura.

### Fase 4: Limpeza (Arquivamento)
*   **Ação:** Movemos `core`, `pwa`, `my-ide` para `_archive/`.
*   **Porquê:** Reduzir a carga cognitiva. O desenvolvedor (e a IA) agora só precisa olhar para `ia_core` e `ticonta`.

---

## 🗺️ Para Onde Vamos (Próximos Passos)

1.  **Conexão Inteligente (Agentes)**
    *   *Status:* Os endpoints `/api/chat` e `/api/tradutor` existem mas usam lógica simulada (mock).
    *   *Meta:* Conectar a lógica real do `academia_manager.py` (agora em arquivo) para dentro destes endpoints.

2.  **Sincronização de Dados**
    *   *Status:* Dados salvos em JSON local (`data/`).
    *   *Meta:* Criar um mecanismo de sync para quando o PWA voltar a ter internet, enviar os dados locais para a nuvem (Supabase ou SQLite no disco).

3.  **TiConta PWA**
    *   *Status:* Ainda é um projeto React separado.
    *   *Meta:* Integrar o build do TiConta dentro de `static/platforms/ticonta` para unificar tudo sob o mesmo domínio.

---

## 📂 Estrutura Atual (Mapa)

```text
/mnt/carpintaria_os/
├── ia_core/                  (RAIZ DO SISTEMA)
│   ├── main.py               (Servidor API)
│   ├── vercel.json           (Config Vercel)
│   ├── data/                 (JSONs de dados)
│   ├── static/               (Frontend)
│   │   ├── dumbanengue.html  (Store/Portfolio)
│   │   ├── Escritorio.html   (Gestão)
│   │   ├── Studio.html       (IDE)
│   │   └── platforms/        (PWAs Independentes)
│   │       ├── txiling/
│   │       ├── academia/
│   │       ├── market/
│   │       └── saude/
│   └── api/                  (Entrypoint Vercel)
├── ticonta/                  (ERP React - Separado)
└── _archive/                 (Código Antigo - Backup)
```

**Este sistema está pronto para crescer.**

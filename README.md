<h1 align="center">🎵 MelodyBot</h1>

<p align="center">
  <strong>O bot de música paraense — agora em Python.</strong><br/>
  Slash commands, fila, controles por botão e uma camada de monetização (Free / Premium).
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/discord.py-2.7-5865F2?logo=discord&logoColor=white" alt="discord.py" />
  <img src="https://img.shields.io/badge/license-MIT-yellow" alt="MIT" />
</p>

---

## ✨ Features

- 🎧 **Slash commands** modernos: `/play`, `/skip`, `/stop`, `/pause`, `/resume`, `/queue`, `/nowplaying`, `/loop`
- 🎛️ **Controles por botão** no "tocando agora" (play/pause, skip, stop)
- 📜 **Fila** por servidor, com loop de faixa/fila
- 🔎 Busca por nome ou URL via **yt-dlp** (sem Lavalink — roda num processo só)
- 💳 **Monetização**: planos Free/Premium com gate de features
- 🗄️ Persistência em **SQLite** (zero infra)
- 🐳 **Docker** pronto para deploy

## 🎚️ Comandos

| Comando | Descrição |
|---|---|
| `/play <busca ou url>` | Toca ou adiciona à fila |
| `/skip` | Pula a faixa atual |
| `/stop` | Para tudo e limpa a fila |
| `/pause` `/resume` | Pausa / retoma |
| `/queue` | Mostra a fila |
| `/nowplaying` | Faixa atual |
| `/loop <off\|track\|queue>` | Modo de repetição |
| `/plan` | Plano atual do servidor |
| `/premium` | Assina o Premium |

## 🚀 Rodando localmente

Requisitos: **Python 3.11+** e **FFmpeg** instalado.

```bash
cp .env.example .env      # preencha o DISCORD_TOKEN
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m melodybot
```

Para desenvolvimento, defina `DEV_GUILD_IDS` no `.env` com o ID do seu servidor
de testes — os slash commands aparecem na hora (o sync global leva até 1h).

## 🐳 Docker

```bash
docker compose up --build
```

O FFmpeg já vem na imagem e o SQLite é persistido num volume.

## 💳 Monetização (Free / Premium)

O bot funciona 100% sem pagamentos. Se quiser habilitar o Premium:

| Plano | Fila | Duração/faixa | Filtros | Playlists |
|---|---|---|---|---|
| **Free** | limitada (`FREE_QUEUE_LIMIT`) | limitada | ❌ | ❌ |
| **Premium** | ilimitada | sem limite | ✅ | ✅ |

O gateway é **plugável**. Hoje há suporte a **Mercado Pago** (Pix + cartão):

```env
PAYMENT_PROVIDER=mercadopago
MERCADOPAGO_ACCESS_TOKEN=seu_token       # nunca comite isso
PAYMENT_WEBHOOK_BASE_URL=https://seu-host
```

Fluxo: `/premium` gera um checkout → usuário paga → o Mercado Pago chama
`POST /webhook/mercadopago` → o servidor ativa o Premium do servidor por 30 dias.
As credenciais vêm **só de variáveis de ambiente** — nada de chave no repositório.

Para adicionar outro gateway (Stripe, etc.), implemente `PaymentProvider`
em `melodybot/payments/` e registre no factory.

## ☁️ Hospedagem

Um bot de música fica **sempre ligado** (é um worker, não um site que dorme),
o que torna difícil hospedar 100% de graça de forma duradoura. Panorama honesto:

- **VPS própria / máquina em casa** — mais barato e sem surpresa; roda o `docker compose`.
- **Fly.io** — não tem mais free tier permanente (apenas trial); depois é pay-as-you-go, geralmente centavos para 1 bot pequeno.
- **Oracle Cloud Free Tier** — VM "Always Free" (ARM) é a opção gratuita mais durável hoje; suba o Docker nela.
- **Railway / Render** — free tiers costumam dormir ou limitar horas, o que derruba a reprodução.

Recomendação: **Oracle Always Free** (grátis e não dorme) ou uma VPS barata.
A imagem Docker roda igual em qualquer um.

## 🧪 Qualidade

```bash
pip install -r requirements-dev.txt
ruff check .
pytest -q
```

CI roda lint + testes a cada push/PR (`.github/workflows/ci.yml`).

## 📂 Estrutura

```
melodybot/
  __main__.py        entrypoint (python -m melodybot)
  bot.py             classe do bot, junta tudo
  config.py          settings via .env
  database.py        repository SQLite (unico lugar com SQL)
  plans.py           planos e limites de features
  webhook.py         servidor aiohttp de confirmacao de pagamento
  music/             track (yt-dlp), player (fila), manager
  payments/          provider abstrato + mercadopago + noop
  cogs/              music (slash commands) + premium
```

Feito por [Anderson Lima](https://github.com/jubureba) · Licença MIT

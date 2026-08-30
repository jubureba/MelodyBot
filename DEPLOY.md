# Deploy do MelodyBot (24/7)

Um bot de música fica **sempre ligado** (é um worker, não um site que dorme).
Abaixo, o caminho gratuito mais durável e a alternativa em VPS.

## Opção recomendada: Oracle Cloud — Always Free

A Oracle oferece uma VM ARM "Always Free" que **não dorme** e é suficiente
para 1 bot pequeno. Passos:

1. Crie a conta em https://www.oracle.com/cloud/free/ e provisione uma
   instância **VM.Standard.A1.Flex** (Ubuntu 22.04), dentro do Always Free.
2. Instale Docker na VM:
   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER   # relogue depois
   ```
3. Envie o projeto (git clone do repo) e crie o `.env` a partir do
   `.env.example`, preenchendo as chaves (veja abaixo).
4. Suba:
   ```bash
   docker compose up -d --build
   ```
5. Logs: `docker compose logs -f`

O SQLite é persistido no volume `melodybot-data`, então planos e histórico
sobrevivem a reinícios.

## Variáveis de ambiente (`.env`)

Obrigatória:
- `DISCORD_TOKEN` — token do bot (Discord Developer Portal).

Opcionais (features Premium/IA):
- `PAYMENT_PROVIDER=mercadopago` + `MERCADOPAGO_ACCESS_TOKEN` — habilita `/premium`.
- `AI_PROVIDER=gemini` + `GEMINI_API_KEY` — habilita `/vibe` e `/autoplay`.
- `PAYMENT_WEBHOOK_BASE_URL` — URL pública desta VM (para o webhook de pagamento).

> Sem as opcionais, o bot roda normal no plano Free. Nunca comite chaves.

## Webhook de pagamento

Se usar pagamento, o Mercado Pago precisa alcançar
`https://SEU_HOST/webhook/mercadopago`. Na Oracle/VPS, exponha a porta
(`WEBHOOK_PORT`, padrão 8080) e configure `PAYMENT_WEBHOOK_BASE_URL` com o
domínio/IP público. Para HTTPS, use um proxy (Caddy/Nginx) na frente.

## Alternativa: VPS barata

Qualquer VPS (Hetzner, Contabo, DigitalOcean) roda o mesmo `docker compose`.
É a opção mais previsível se o Always Free da Oracle não estiver disponível na
sua região.

## Sobre Fly.io / Railway / Render

- **Fly.io**: não tem mais free tier permanente (apenas trial); depois é
  pay-as-you-go (centavos para 1 bot).
- **Railway / Render**: free tiers costumam dormir/limitar horas, o que
  interrompe a reprodução. Não recomendados para bot de música 24/7.

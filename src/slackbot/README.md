# How to deploy the Nesta Way Slackbot v1

## 1. Install Skypilot in  new or existing environment

Poetry: `poetry add "skypilot=0.4.1" --group slackbot`

pip: `pip install "skypilot==0.4.1"`

## 2. Export corresponding env vars

```bash
export OPENAI_API_KEY= #<OpenAI API key>
export QDRANT_URL= #<Qdrant cluster URL>
export QDRANT_API_KEY= #<Qdrant API key>
export QDRANT_COLLECTION_NAME=nesta_way_bge-base-v1.5-en_big-chunks # <Replace with collection>
export SLACK_APP_TOKEN= #<Slack App Token>
export SLACK_BOT_TOKEN= #<Slackbot Token>
```

## 3. Run below script in project root and confirm prompt

```bash
sky launch -c slackbot \
    --env SLACK_BOT_TOKEN --env SLACK_APP_TOKEN \
    --env QDRANT_URL --env QDRANT_API_KEY --env QDRANT_COLLECTION_NAME \
    --env OPENAI_API_KEY --env TOKENIZERS_PARALLELISM=true \
    --use-spot \
    ./infra/skypilot/serve_slackbot_eu-west-2.yaml
```

## ***Remember to turn down unused instances: `sky down slackbot`***

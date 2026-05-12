import os
import json
from datetime import date, timedelta
from flask import Flask, request, jsonify, Response
from garminconnect import Garmin

app = Flask(__name__)

GARMIN_EMAIL = os.environ.get("GARMIN_EMAIL")
GARMIN_PASSWORD = os.environ.get("GARMIN_PASSWORD")
AUTH_KEY = os.environ.get("AUTH_KEY")

_garmin_client = None

def get_client():
    global _garmin_client
    if _garmin_client is None:
        _garmin_client = Garmin(GARMIN_EMAIL, GARMIN_PASSWORD)
        _garmin_client.login()
    return _garmin_client

def safe_call(fn, *args, **kwargs):
    global _garmin_client
    try:
        return fn(*args, **kwargs)
    except Exception:
        _garmin_client = None
        client = get_client()
        return fn(*args, **kwargs)

TOOLS = [
    {
        "name": "get_activities",
        "description": "Lista as atividades (treinos executados) mais recentes. Parametro: limit (int, padrao 10).",
        "inputSchema": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "default": 10}}
        }
    },
    {
        "name": "get_activities_by_date",
        "description": "Atividades em um intervalo de datas. Parametros obrigatorios: start_date e end_date (YYYY-MM-DD).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string"},
                "end_date": {"type": "string"}
            },
            "required": ["start_date", "end_date"]
        }
    },
    {
        "name": "get_activity_details",
        "description": "Metricas detalhadas de uma atividade especifica. Parametro: activity_id.",
        "inputSchema": {
            "type": "object",
            "properties": {"activity_id": {"type": "string"}},
            "required": ["activity_id"]
        }
    },
    {
        "name": "get_activity_splits",
        "description": "Splits (parciais por km/milha) de uma atividade. Parametro: activity_id.",
        "inputSchema": {
            "type": "object",
            "properties": {"activity_id": {"type": "string"}},
            "required": ["activity_id"]
        }
    },
    {
        "name": "get_activity_hr_zones",
        "description": "Tempo gasto em cada zona de frequencia cardiaca. Parametro: activity_id.",
        "inputSchema": {
            "type": "object",
            "properties": {"activity_id": {"type": "string"}},
            "required": ["activity_id"]
        }
    },
    {
        "name": "get_training_plans",
        "description": "Lista todos os planos de treino (Garmin Coach ou customizados).",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_workouts",
        "description": "Lista os treinos salvos (workouts).",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_calendar",
        "description": "Calendario de treinos programados de um mes. Parametros: year (int) e month (int, 1-12).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "year": {"type": "integer"},
                "month": {"type": "integer"}
            },
            "required": ["year", "month"]
        }
    },
    {
        "name": "get_vo2max",
        "description": "VO2 Max de corrida e ciclismo para uma data. Parametro opcional: target_date (YYYY-MM-DD).",
        "inputSchema": {
            "type": "object",
            "properties": {"target_date": {"type": "string"}}
        }
    },
    {
        "name": "get_training_status",
        "description": "Status de treinamento atual (produtivo, mantendo, destreinando, pico, recuperacao, overreaching).",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_training_readiness",
        "description": "Prontidao para treinar. Parametro opcional: target_date (YYYY-MM-DD).",
        "inputSchema": {
            "type": "object",
            "properties": {"target_date": {"type": "string"}}
        }
    },
    {
        "name": "get_personal_records",
        "description": "Recordes pessoais: melhor 5K, 10K, meia maratona, maratona, maior corrida, etc.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_race_predictions",
        "description": "Previsao de tempo de prova para 5K, 10K, meia maratona e maratona baseada na sua forma atual.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_lactate_threshold",
        "description": "Limiar de lactato: FC e ritmo no limiar.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_daily_summary",
        "description": "Resumo diario completo: passos, calorias totais e ativas, distancia, andares, minutos ativos, FC repouso. Parametro opcional: target_date (YYYY-MM-DD), padrao hoje.",
        "inputSchema": {
            "type": "object",
            "properties": {"target_date": {"type": "string"}}
        }
    },
    {
        "name": "get_daily_steps_range",
        "description": "Passos diarios em um intervalo de datas. Parametros obrigatorios: start_date e end_date (YYYY-MM-DD).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string"},
                "end_date": {"type": "string"}
            },
            "required": ["start_date", "end_date"]
        }
    },
    {
        "name": "get_hydration",
        "description": "Hidratacao (ingestao de agua) para uma data. Parametro opcional: target_date (YYYY-MM-DD).",
        "inputSchema": {
            "type": "object",
            "properties": {"target_date": {"type": "string"}}
        }
    },
    {
        "name": "get_endurance_score",
        "description": "Endurance Score: avaliacao da capacidade aerobica acumulada.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_hill_score",
        "description": "Hill Score: avaliacao da capacidade de subida e descida.",
        "inputSchema": {"type": "object", "properties": {}}
    }
]

def call_tool(name, args):
    client = get_client()
    args = args or {}
    today = date.today().isoformat()

    if name == "get_activities":
        limit = args.get("limit", 10)
        return safe_call(client.get_activities, 0, limit)

    if name == "get_activities_by_date":
        return safe_call(client.get_activities_by_date, args["start_date"], args["end_date"])

    if name == "get_activity_details":
        return safe_call(client.get_activity, args["activity_id"])

    if name == "get_activity_splits":
        return safe_call(client.get_activity_splits, args["activity_id"])

    if name == "get_activity_hr_zones":
        return safe_call(client.get_activity_hr_in_timezones, args["activity_id"])

    if name == "get_training_plans":
        return safe_call(client.get_training_plans)

    if name == "get_workouts":
        return safe_call(client.get_workouts)

    if name == "get_calendar":
        return safe_call(client.get_calendar, args["year"], args["month"])

    if name == "get_vo2max":
        target = args.get("target_date", today)
        return safe_call(client.get_max_metrics, target)

    if name == "get_training_status":
        return safe_call(client.get_training_status, today)

    if name == "get_training_readiness":
        target = args.get("target_date", today)
        return safe_call(client.get_training_readiness, target)

    if name == "get_personal_records":
        return safe_call(client.get_personal_record)

    if name == "get_race_predictions":
        return safe_call(client.get_race_predictions)

    if name == "get_lactate_threshold":
        return safe_call(client.get_lactate_threshold)

    if name == "get_daily_summary":
        target = args.get("target_date", today)
        return safe_call(client.get_stats_and_body, target)

    if name == "get_daily_steps_range":
        return safe_call(client.get_daily_steps, args["start_date"], args["end_date"])

    if name == "get_hydration":
        target = args.get("target_date", today)
        return safe_call(client.get_hydration_data, target)

    if name == "get_endurance_score":
        return safe_call(client.get_endurance_score, today)

    if name == "get_hill_score":
        return safe_call(client.get_hill_score, today)

    raise ValueError("Ferramenta desconhecida: " + name)

def json_rpc(id_, result=None, error=None):
    body = {"jsonrpc": "2.0", "id": id_}
    if error is not None:
        body["error"] = error
    else:
        body["result"] = result
    return jsonify(body)

@app.route("/", methods=["GET"])
def index():
    key = request.args.get("key")
    if not AUTH_KEY or ke

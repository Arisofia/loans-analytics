import logging

logger = logging.getLogger(__name__)

def process_chat_response(response):
    """Procesa la respuesta de la API de Gemini de forma segura."""
    try:
        if not response:
            raise ValueError("Empty response received")
        return response.get('choices', {}).get('message', '')
    except KeyError as e:
        logger.error(f"Formato de respuesta inválido: {e}")
        return None
    except Exception as e:
        logger.critical(f"Error inesperado en integración Gemini: {e}")
        raise e

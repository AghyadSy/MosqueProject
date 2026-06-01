from rest_framework.renderers import JSONRenderer

class ForceAsciiJSONRenderer(JSONRenderer):
    ensure_ascii = True
    charset = 'utf-8'
    media_type = 'application/json'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        # Explicitly call super and ensure it's ASCII
        response = super().render(data, accepted_media_type, renderer_context)
        return response
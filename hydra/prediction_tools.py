"""Read-only hypothesis RPC; outcomes are measured by the host, not the model."""


def install(namespace, send, receive):
    def request(operation, **fields):
        send(dict(type='hydra_prediction', request=dict(operation=operation, **fields)))
        reply = receive()
        if reply.get('type') != 'hydra_prediction_result':
            raise ValueError(str(reply.get('error', 'Prediction RPC failed')))
        return reply['result']

    def prediction_start(models, features, question=''):
        return request('start', models=models, features=features, question=question)

    def prediction_forecast(probes):
        return request('forecast', probes=probes)

    def prediction_status():
        return request('status')

    def prediction_discard():
        return request('discard')

    namespace.update(prediction_start=prediction_start, prediction_forecast=prediction_forecast,
                     prediction_status=prediction_status, prediction_discard=prediction_discard)

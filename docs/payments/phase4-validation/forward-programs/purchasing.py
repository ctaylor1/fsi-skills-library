from pathlib import Path
D=Path(__file__).resolve().parent
exec((D/'exercise.py').read_text().split('# Independently authored economic dossier:')[0])
seeds=json.loads((D/'seed-requests.json').read_text());request=deepcopy(seeds['card']);request['data']['program_type']='purchasing'
run('commercial-purchasing-normal','commercial-payment-workflow-designer','validate_commercial_card_input.py','review_commercial_card.py',request)
request['data']['attempts'][2].pop('purchase_order_ref')
run('commercial-purchasing-order-missing','commercial-payment-workflow-designer','validate_commercial_card_input.py','review_commercial_card.py',request)
(D/'commands-supplement.json').write_text(json.dumps(commands,indent=2)+'\n')

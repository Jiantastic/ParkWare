import httplib2, argparse, os, sys, json, math
from oauth2client import tools, file, client
from googleapiclient import discovery
from googleapiclient.errors import HttpError

project_id = "ichackathon"
model_id = "training1"

inputFile = "Data/TrainingTest23.csv"

def train_model():
	api = get_prediction_api(False)
	print("Training model")
	iBody = {
		"id": model_id,
		"storageDataLocation": "trainingset2_ichack/TrainingSet1.csv",
		"modelType": "regression"
	}
	api.trainedmodels().insert(project=project_id, body = iBody).execute()

def analyse_model():
	api = get_prediction_api(False)
	analysis = api.trainedmodels().analyze(project=project_id, id = model_id).execute()
	confusionMatrix = analysis.get('modelDescription')['confusionMatrix']
	print(confusionMatrix)

def check_if_ready():
	api = get_prediction_api(False)
	model = api.trainedmodels().get(project=project_id, id=model_id).execute()
	if model.get('trainingStatus') != 'DONE':
		print ('Still training \n Run again after a while')
		exit()
	print ('Model is ready')
	make_prediction()

def make_prediction():
	api = get_prediction_api(False)
	with open(inputFile) as file:
		record = file.readline().split(',')
	iBody = {
		'input': {
					'csvInstance':record
				 }
	}
	prediction = api.trainedmodels().predict(project=project_id, id=model_id, body=iBody).execute()
	
	finalPrediction = prediction.get('outputValue')
	#probabilities = prediction.get('outputMulti')
	print(finalPrediction)
	#print(probabilities)

def get_prediction_api(service_account=True):
	scope = [
		'https://www.googleapis.com/auth/prediction',
		'https://www.googleapis.com/auth/devstorage.read_only'
	]
	return get_api('prediction', scope, service_account)

def get_api(api, scope, service_account=True):
	""" Build API client based on oAuth2 authentication """
	STORAGE = file.Storage('oAuth2.json') #local storage of oAuth tokens
	credentials = STORAGE.get()
	if credentials is None or credentials.invalid: #check if new oAuth flow is needed
		if service_account: #server 2 server flow
			with open('service_account.json') as f:
				account = json.loads(f.read())
				email = account['client_email']
				key = account['private_key']
			credentials = client.SignedJwtAssertionCredentials(email, key, scope=scope)
			STORAGE.put(credentials)
		else: #normal oAuth2 flow
			CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secrets.json')
			FLOW = client.flow_from_clientsecrets(CLIENT_SECRETS, scope=scope)
			PARSER = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, parents=[tools.argparser])
			FLAGS = PARSER.parse_args(sys.argv[1:])
			credentials = tools.run_flow(FLOW, STORAGE, FLAGS)
		
	#wrap http with credentials
	http = credentials.authorize(httplib2.Http())
	return discovery.build(api, "v1.6", http=http)

def main():
	try:
		check_if_ready()
	except HttpError as e:
		if e.resp.status == 404:
			print("Model doesn't exist")
			train_model()
			check_if_ready()
		else:
			print(e)

if __name__ == '__main__':
	main()

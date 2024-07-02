from pprint import pprint
import argparse
from prefect import flow, get_run_logger

from prefect.deployments import Deployment
from prefect.infrastructure import Process

from sous_chef import RunPipeline, recipe_loader
import statsd

statsd_url = "statsd://stats.tarbell.mediacloud.org"
stats_directory = "metrics/query-benchmark/"

@flow()
def RunMetrics(test=False):
	mixins_file = open("queries.yaml", "r")
	recipe_file = open("QueryRecipe.yaml").read()

	mixins = recipe_loader.load_mixins(mixins_file)
	if test:
		mixins = [mixins[0]]
	
	run_data = {}
	for template_params in mixins:
		json_conf = recipe_loader.t_yaml_to_conf(recipe_file, **template_params)
		json_conf["name"] = template_params["NAME"]

		results = RunPipeline(json_conf)
		
		run_data[template_params["NAME"]] = list(results.values())
	
	statsd_client = statsd.StatsdClient(
		statsd_url, None, stats_directory)

	for name, value in run_data.items():
		print(f"{name}:{value}")
		statsd_client.timing(name, value)

	###Then I think we want to report a timing metric to statsd for each of these runs? is that right?


	

if __name__ == "__main__":
	
	#Continually annoyed by building images in prefect. 
	#Not sure how to get the requirements into this image here in a way that feels nice to include as code. 
	parser = argparse.ArgumentParser()
	parser.add_argument("-t", "--test", action='store_true')
	args = parser.parse_args()
	RunMetrics(args.test)




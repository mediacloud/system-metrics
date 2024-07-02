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
	logger = get_run_logger()
	statsd_client = statsd.StatsdClient(
		statsd_url, None, stats_directory)

	mixins_file = open("queries.yaml", "r")
	recipe_file = open("QueryRecipe.yaml").read()

	mixins = recipe_loader.load_mixins(mixins_file)
	if test:
		mixins = [mixins[0]]
	

	run_data = {}
	for template_params in mixins:
		json_conf = recipe_loader.t_yaml_to_conf(recipe_file, **template_params)
		json_conf["name"] = template_params["NAME"]

		#run. that. pipeline!!!
		results = RunPipeline(json_conf)

		name = template_params["NAME"]
		
		elapsed = list(results.values())[0]["ElapsedTime"]
		run_data[name] = elapsed

		#Actually report the data here
		logger.info(f"{name}:{elapsed}")
		statsd_client.timing(name, elapsed)

	print(run_data)


	

if __name__ == "__main__":
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-t", "--test", action='store_true')
	args = parser.parse_args()
	RunMetrics(args.test)




from pprint import pprint
import argparse
from prefect import flow, get_run_logger

from prefect.deployments import Deployment
from prefect.infrastructure import Process

from sous_chef import RunPipeline, recipe_loader
import statsd

statsd_url = "stats.tarbell.mediacloud.org"

prod_stats_directory = "mc.prod.system-metrics"
staging_stats_directory = "mc.staging.system-metrics"

@flow()
def RunMetrics(test=False, staging_only=False):
	logger = get_run_logger()
	statsd_client = statsd.StatsdClient(
		statsd_url, None, prod_stats_directory)

	mixins_file = open("queries.yaml", "r")
	recipe_file = open("QueryRecipe.yaml").read()

	mixins = recipe_loader.load_mixins(mixins_file)
	if test:
		mixins = [mixins[0]]
	
	if not staging_only:
		#For Prod
		run_data = {}
		for template_params in mixins:
			template_params["STAGING"] = False
			json_conf = recipe_loader.t_yaml_to_conf(recipe_file, **template_params)
			json_conf["name"] = template_params["NAME"]

			#run. that. pipeline!!!
			results = RunPipeline(json_conf)

			name = template_params["NAME"]
			if(len(results) > 0):
				elapsed = list(results.values())[0]["ElapsedTime"]
				run_data[name] = elapsed

				#Actually report the data here
				logger.info(f"{name}:{elapsed}")
				statsd_client.timing(name, elapsed)

	
	
	statsd_client = statsd.StatsdClient(
		statsd_url, None, staging_stats_directory)

	#For Staging
	run_data = {}
	for template_params in mixins:
		template_params["STAGING"] = True
		json_conf = recipe_loader.t_yaml_to_conf(recipe_file, **template_params)
		json_conf["name"] = template_params["NAME"]

		#run. that. pipeline!!!
		results = RunPipeline(json_conf)

		name = template_params["NAME"]
		if(len(results) > 0):
			elapsed = list(results.values())[0]["ElapsedTime"]
			run_data[name] = elapsed

			#Actually report the data here
			logger.info(f"{name}:{elapsed}")
			statsd_client.timing(name, elapsed)

	

if __name__ == "__main__":
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-t", "--test", action='store_true')
	args = parser.parse_args()
	RunMetrics(args.test)




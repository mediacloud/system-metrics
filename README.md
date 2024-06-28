
System using sous-chef to run daily timing metrics on mediacloud services. 

Is this an excersize over-engineering? 
Yes absolutely- but it's a nice demonstration of how to fold sous-chef into a custom interface. 

Running `prefect deploy` in this directory creates a deployment in prefect cloud. 

Pet peeve here is having three .yaml files - should look into how I might have instantiated the flow without the yaml files, just defining in in the main source code...
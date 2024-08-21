# LAA Shared IP Allow list
The list is intended to be pulled into applications for adding allow lists to IP-restricted areas. This should not be seen as a primary level of protection.

## Usage
The list can be pulled from this URL: https://raw.githubusercontent.com/ministryofjustice/laa-ip-allowlist/main/cidrs.txt

This can be done using your Helm chart, bash scripts, pipeline configuration or any method that works best for you. For safety of your application, in case of failure or bad formatting in the list, please only pull the list as part of deployment and not as part of the application runtime code. This should be structured in a way that if the deployment fails then it doesn't affect the existing application on production. E.g. Through Kubernetes deployment or helm charts through Github actions and Circle CI. 

### Examples:

Using bash script combined with Helm Chart: ministryofjustice/cla_public#1276

## Maintenance
Please update the list without any spaces and comments. Use one IP range per line.

from kubernetes import client, config, watch
import logging
import sys

logger = logging.getLogger('pinghost-controller')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def create_ping_pod(host: str, name: str) -> dict:
    pod_name = f"pinghost-{name}"
    pod_manifest = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": pod_name
        },
        "spec": {
            "containers": [{
                "name": "ping",
                "image": "busybox",
                "command": ["sh", "-c", f"ping {host}"]
            }],
            "restartPolicy": "Never"
        }
    }
    return pod_manifest


def main():
    config.load_incluster_config()
    logger.info("Starting pinghost controller")

    api = client.CustomObjectsApi()
    logger.info("Connected to Kubernetes API")
    pod_v1 = client.CoreV1Api()
    logger.info("Connected to Kubernetes Core API")
    namespace = "default"

    resource_version = ''
    while True:
        stream = watch.Watch().stream(api.list_namespaced_custom_object,
                                      group="xmp.io",
                                      version="v1",
                                      namespace=namespace,
                                      plural="pinghosts",
                                      resource_version=resource_version)
        for event in stream:
            logger.debug(f"Event: {event}")
            resource_version = event['object']['metadata']['resourceVersion']
            if event['type'] == 'ADDED':
                logger.info(f"New pinghost added: {event['object']['metadata']['name']}")
                host = event['object']['spec']['host']
                name = event['object']['metadata']['name']
                pod_manifest = create_ping_pod(host, name)
                try:
                    pod_v1.create_namespaced_pod(namespace=namespace, body=pod_manifest)
                    logger.info(f"Created pod for host: {host}")
                except client.exceptions.ApiException as e:
                    logger.error(f"Exception when creating pod: {e}")
            elif event['type'] == 'DELETED':
                logger.info(f"Pinghost deleted: {event['object']['metadata']['name']}")
                name = event['object']['metadata']['name']
                pod_name = f"pinghost-{name}"
                try:
                    pod_v1.delete_namespaced_pod(name=pod_name, namespace=namespace)
                    logger.info(f"Deleted pod: {pod_name}")
                except client.exceptions.ApiException as e:
                    logger.error(f"Exception when deleting pod: {e}")
            elif event['type'] == 'MODIFIED':
                logger.info(f"Pinghost modified: {event['object']['metadata']['name']}")
                host = event['object']['spec']['host']
                name = event['object']['metadata']['name']
                pod_manifest = create_ping_pod(host, name)
                pod_name = f"pinghost-{name}"
                try:
                    pod_v1.replace_namespaced_pod(name=pod_name, namespace=namespace, body=pod_manifest)
                    logger.info(f"Updated pod for host: {host}")
                except client.exceptions.ApiException as e:
                    logger.error(f"Exception when updating pod: {e}")


if __name__ == "__main__":
    main()

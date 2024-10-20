To install run the following command:

```bash
kubectl apply -f pinghost-native.yml
```

To build the controller image, run the following command:

```bash
cd pinghost-controller
docker build -d pinghost-controller:<tag> .
```

The app works in the following way:

1. A custom resource definition (CRD) is created for the `PingHost` resource.
2. The controller watches for `PingHost` resources and creates a `Pod` for each `PingHost` resource.
3. The `Pod` runs a container that pings the host specified in the `PingHost` resource.
4. The controller updates the pod if the `PingHost` resource is updated.
5. If the PingHost resource is deleted, the controller deletes the corresponding Pod.

This is the strtucture of the `PingHost` resource:

```yaml
apiVersion: xmp.io/v1
kind: PingHost
metadata:
  name: name_of_the_host
spec:
  host: "ip or domain"
```

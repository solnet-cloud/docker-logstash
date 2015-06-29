# docker-logstash

Logstash is a flexible, open source data collection, parsing, and enrichment pipeline. With connectors to common infrastructure for easy integration, Logstash is designed to efficiently process a growing list of log, event, and unstructured data sources for distribution into a variety of outputs, including Elasticsearch.

More details on the Logstash product can be found at the elastic website at https://www.elastic.co/products/logstash

This Docker build builds on top of a Java image to provide a working Logstash instance to connect to your Elasticsearch instance.

Under the most basic usage you will make sure it is operating in the same network (i.e. same machine) as the cluster it will be connected to. It is recommened you use restart on-failure, prevent swaping, and limit RAM usage of the container to just over 4GiB.

    docker run -d --restart=on-failure --memory="6442450944" --memory-swap="-1" solnetcloud/logstash:latest

Please note that if you need a Lumberjack interface you will need to provide an SSL certificate --lm-ssl-crt and --lm-ssl-key. Lumberjack in this configuration requires JSON input and will be available on port 8888.

NOTICE: As this build is designed to run using multicast it is recommend you utilise Weave, or bridge your docker0 on a common subnet in order to facilate the multicast. If you require unicast please override the configuration file

WARNING: DO NOT OUTPUT LOGS TO SYSLOG FOR THIS CONTAINER. Especially if a stdout logging is enabled. This could create a feedback loop where events are processed multiple times.

WARNING: Please note that as syslog is a very muddy term this input only supports RFC3164 syslog with some small modifications. The date format is allowed to be RFC3164 style or ISO8601. Otherwise the rest of RFC3164 must be obeyed. If you do not use RFC3164, DO NOT USE this input.


    usage: entry [-h] [--stdout] [--hash-key [HASH_KEY]] [--use-sha512]                                                                                                                                                                          
                [--es-cluster-name [ES_CLUSTER_NAME]]                                                                                                                                                                                           
                [--es-node-name [ES_NODE_NAME]] [--lm-ssl-crt [LM_SSL_CRT]]                                                                                                                                                                     
                [--lm-ssl-key [LM_SSL_KEY]] [--lm-type [LM_TYPE]]                                                                                                                                                                               
                [--lm-tags [LM_TAGS [LM_TAGS ...]]] [--ignore-match-errors]                                                                                                                                                                     
                                                                                                                                                                                                                                                
    optional arguments:                                                                                                                                                                                                                          
    -h, --help            show this help message and exit                                                                                                                                                                                      
    --stdout              Also output logs processed to stdout for debug (Not                                                                                                                                                                  
                            Recommend)
    --raw, -r             Tell Logstash to use the raw input rather than the
                            syslog input.
                                                                                                                                                                                                                                                
    hashing:                                                                                                                                                                                                                                     
    Arguments specific to hashing                                                                                                                                                                                                              
                                                                                                                                                                                                                                                
    --hash-key [HASH_KEY], -k [HASH_KEY]                                                                                                                                                                                                       
                            The hash key used by Logstash. (Make sure it is
                            consistent when running multiple instances) (Default
                            "docker-logstash")
    --use-sha512, -5      By default this container uses SHA256 for hashing,
                            override and use SHA512.

    elasticsearch:
    Arguments specific to connecting to Elasticsearch

    --es-cluster-name [ES_CLUSTER_NAME], -c [ES_CLUSTER_NAME]
                            The name of the cluster the Elasticsearch Instance
                            should connect to
    --es-node-name [ES_NODE_NAME], -n [ES_NODE_NAME]
                            The node name this logstash node should use when
                            connecting to Elasticsearch

    lumberjack:
    Arguments for when you want to use Lumberjack input

    --lm-ssl-crt [LM_SSL_CRT], -R [LM_SSL_CRT]
                            Certificate for SSL termination, under the /ls-
                            data/ssl/ volume
    --lm-ssl-key [LM_SSL_KEY], -K [LM_SSL_KEY]
                            SSL Key for SSL termination, under the /ls-data/ssl/
                            volume
    --lm-type [LM_TYPE], -T [LM_TYPE]
                            If you want the lumberjack messages to have a specific
                            type, state it here
    --lm-tags [LM_TAGS [LM_TAGS ...]], -t [LM_TAGS [LM_TAGS ...]]
                            If you want the lumberjack messages to have tags
                            applied, state them here
    --ignore-match-errors
                            Ignore SSL certificate match errors. (Not recommended)


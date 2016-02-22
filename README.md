# SMATCH Tools
VisualSMATCH and AMR ensemble voting tool based on [SMATCH](http://amr.isi.edu/evaluation.html).

It provides user interface for computed SMATCH results, it also employs [C6.0](http://c60.ailab.lv/) classifier to show systematic (mis)alignments (as rules) between triplets of AMR graphs as seen by SMATCH.

To run install [docker](https://www.docker.com/) first and execute in terminal:

```
$ ./vsmatch.sh
```
Point your browser either to [http://localhost:9000](http://localhost:9000) or the URL that is shown on screen (in case you are not running it under Linux).

### Building docker image from source
To build your own image, inside project directory execute:

```
$ docker build -t <yourimagename> .
```
and run container using:

```
$ docker run -it -p 9000:9000 <yourimagename>
```

Note that, if not running under Linux, IP address can be obtained using:

```
$ docker-machine ip default
```
where ```default``` is docker machine name.


# Used Tools and Resources
[Bottle](http://bottlepy.org) (micro web-framework for Python) fork from [github.com/mrdon/bottle](https://github.com/mrdon/bottle).<br/>
[SMATCH](http://amr.isi.edu/evaluation.html) (updated version [here](http://alt.qcri.org/semeval2016/task8/index.php?id=data-and-tools)). <br/>
[AMR Bank](http://amr.isi.edu/download/amr-bank-struct-v1.5.txt) as sample data.

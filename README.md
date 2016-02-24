# SMATCH Tools
VisualSMATCH and AMR ensemble voting tool based on [SMATCH](http://amr.isi.edu/evaluation.html).

Ready to run [docker](https://www.docker.com/) image available at dockerhub:

```
docker run -it -p 9000:9000 didzis/visualsmatch
```
On Linux open [http://localhost:9000](http://localhost:9000), on MacOS X or Windows open [http://192.168.99.100:9000](http://192.168.99.100:9000). Alternatively, execute: ```$ ./vsmatch.sh``` and point your browser to the URL that is shown on the screen.

# Description
VisualSMATCH provides user interface for computed SMATCH results, it also employs [C6.0](http://c60.ailab.lv/) classifier to show systematic (mis)alignments (as rules) between triplets of AMR graphs as seen by SMATCH.
For details see:

```
@InProceedings{gbarzdins-dgosko:2016:NAACL-HLT,
  author    = {Barzdins, Guntis and  Gosko, Didzis},
  title     = {RIGA: Impact of Smatch Extensions and Character-Level Neural Translation on AMR Parsing Accuracy},
  booktitle = {Proceedings of the 2016 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies},
  month     = {June},
  year      = {2016},
  address   = {San Diego, California},
  publisher = {Association for Computational Linguistics},
  pages     = {to appear},
  url       = {to appear}
}
```


# Building docker image from source
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

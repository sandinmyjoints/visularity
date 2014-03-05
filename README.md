Visularity
==========

This was created as a proof of concept for a talk I gave, called [An Introduction to Gensim: Topic Modelling for Humans](http://williamjohnbert.com/2012/05/an-introduction-to-gensim-topic-modelling-for-humans/).

It is fairly experimental and rough. Feel free to fork and improve.

Similarity cluster visualization
--------------------------------

Visularity does not come with any of the data needed to do similarity comparison (e.g., transformation models and
dictionaries). This data is generally application-specific and also large (think hundreds of megabytes).
Visit http://radimrehurek.com/gensim to learn how to generate data. It's not that hard.

Requires:
* gensim>=0.8
* scipy>=0.10.1
* hookbox>=0.3.4dev (not on Pypi, try https://github.com/hookbox/hookbox)
* Flask>=0.8
* scikit-learn>=0.10
* requests>=0.11.1
* gensim models and a dictionary -- see http://radimrehurek.com/gensim for how to generate these.
 

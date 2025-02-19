"""
Germeval Task 2017: Shared Task on Aspect-based Sentiment in Social Media Customer Feedback

Paper: https://www.inf.uni-hamburg.de/en/inst/ab/lt/publications/2017-wojatzkietal-germeval2017-workshop.pdf

Huggingface dataset: https://huggingface.co/datasets/malteos/germeval2017

Original dataset: http://ltdata1.informatik.uni-hamburg.de/germeval2017/
"""
import datasets
from lm_eval.base import Task, rf
from lm_eval.metrics import mean


_CITATION = """
@inproceedings{germevaltask2017,
title = {{GermEval 2017: Shared Task on Aspect-based Sentiment in Social Media Customer Feedback}},
author = {Michael Wojatzki and Eugen Ruppert and Sarah Holschneider and Torsten Zesch and Chris Biemann},
year = {2017},
booktitle = {Proceedings of the GermEval 2017 - Shared Task on Aspect-based Sentiment in Social Media Customer Feedback},
address={Berlin, Germany},
pages={1--12}
}
"""


def _germeval2017_agg_precision(items):
    references, predictions = zip(*items)
    precision_metric = datasets.load_metric("precision")
    return precision_metric.compute(
        references=references,
        predictions=predictions,
        average="macro",
    )["precision"]


def _germeval2017_agg_recall(items):
    references, predictions = zip(*items)
    recall_metric = datasets.load_metric("recall")
    return recall_metric.compute(
        references=references,
        predictions=predictions,
        average="macro",
    )["recall"]


def _germeval2017_agg_f1(items):
    references, predictions = zip(*items)
    f1_metric = datasets.load_metric("f1")
    return f1_metric.compute(
        references=references,
        predictions=predictions,
        average="macro",
    )["f1"]


class GermEval2017(Task):
    VERSION = 0
    DATASET_PATH = "malteos/germeval2017"

    # Available test files: test_syn-2017-09-15.csv, test_dia-2017-09-15.tsv
    TEST_FILE = "test_syn-2017-09-15.csv"

    LABEL_TO_INDEX = {
        "positive": 1,
        "negative": -1,
        "neutral": 0,
    }

    def download(self, data_dir=None, cache_dir=None, download_mode=None):
        args = ()
        kwargs = dict(
            path=self.DATASET_PATH,
            name=self.DATASET_NAME,
            data_dir=data_dir,
            cache_dir=cache_dir,
            download_mode=download_mode,
            data_files={
                "train": "train-2017-09-15.csv",
                "test": self.TEST_FILE,
            },
            features=datasets.Features(
                {
                    "id": datasets.Value(dtype="string", id=None),
                    "text": datasets.Value(dtype="string", id=None),
                    "relevance": datasets.Value(dtype="string", id=None),
                    "sentiment": datasets.Value(dtype="string", id=None),
                    "aspect_polarity": datasets.Value(dtype="string", id=None),
                }
            ),
        )
        self._download_pushed(args, kwargs, data_dir, cache_dir, download_mode)

    def has_training_docs(self):
        return True

    def has_validation_docs(self):
        return False

    def has_test_docs(self):
        return True

    def training_docs(self):
        return self.dataset["train"].filter(
            lambda example: example["relevance"] == "True"
            and example["text"] is not None
            and example["sentiment"] in self.LABEL_TO_INDEX
        )

    def test_docs(self):
        # Do NOT filter test set for relevance
        return self.dataset["test"].filter(
            lambda example: example["text"] is not None
            and example["sentiment"] in self.LABEL_TO_INDEX
        )

    def doc_to_text(self, doc):
        return doc["text"] + "\n\nBewertung:"

    def doc_to_target(self, doc):
        if doc["sentiment"] == "positive":
            return " gut"
        elif doc["sentiment"] == "negative":
            return " schlecht"
        else:
            return " neutral"

    def construct_requests(self, doc, ctx):
        """Uses RequestFactory to construct Requests and returns an iterable of
        Requests which will be sent to the LM.

        :param doc:
            The document as returned from training_docs, validation_docs, or
            test_docs.
        :param ctx: str
            The context string, generated by fewshot_context. This includes the natural
            language description, as well as the few shot examples, and the question
            part of the document for `doc`.
        """
        # rf.loglikelihood as the task is a classification problem. For each document the model predicts loglikelihood for the correct label
        # ctx is the fully formatted fewshot example, i.e. K examples + comment to rate

        ll_postive = rf.loglikelihood(ctx, " gut")
        ll_negative = rf.loglikelihood(ctx, " schlecht")
        ll_neutral = rf.loglikelihood(ctx, " neutral")

        return ll_postive, ll_negative, ll_neutral

    def process_results(self, doc, results):
        """Take a single document and the LM results and evaluates, returning a
        dict where keys are the names of submetrics and values are the values of
        the metric for that one document

        :param doc:
            The document as returned from training_docs, validation_docs, or test_docs.
        :param results:
            The results of the requests created in construct_requests.
        """

        ll_postive, ll_negative, ll_neutral = results

        # Evaluation metrics will only work with numerical labels
        if ll_postive[0] > ll_negative[0] and ll_postive[0] > ll_neutral[0]:
            pred = "positive"
        elif ll_negative[0] > ll_postive[0] and ll_negative[0] > ll_neutral[0]:
            pred = "negative"
        else:
            pred = "neutral"

        true_label = self.LABEL_TO_INDEX[doc["sentiment"]]
        pred_label = self.LABEL_TO_INDEX[pred]

        return {
            "acc": pred_label == true_label,
            "precision": (true_label, pred_label),
            "recall": (true_label, pred_label),
            "f1": (true_label, pred_label),
        }

    def aggregation(self):
        """
        :returns: {str: [metric_score] -> float}
            A dictionary where keys are the names of submetrics and values are
            functions that aggregate a list of metric scores
        """

        return {
            "acc": mean,
            "precision": _germeval2017_agg_precision,
            "recall": _germeval2017_agg_recall,
            "f1": _germeval2017_agg_f1,
        }

    def higher_is_better(self):
        return {"acc": True, "precision": True, "recall": True, "f1": True}

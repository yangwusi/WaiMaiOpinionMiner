
import os
import re

import math
from random import choice

from WaiMaiMiner import seg


root_filepath = os.path.dirname(os.path.realpath(__file__))
re_punctuation_split = re.compile(r"([a-zA-Z0-9:\u4e00-\u9fa5]+[，。%、！!？?,；～~.… ]*)")
re_space_split = re.compile(r"\s+")
re_han = re.compile('[\s\u4e00-\u9fa5]+')


class HMMCorpus:
    def __init__(self):
        pass

    @staticmethod
    def _find_final_position(tags, tag, start):
        while start < len(tags):
            if tags[start] != tag:
                break
            start += 1
        return start - 1

    @staticmethod
    def get_corpus(runout_filepath):
        """
            Purpose:
            Get the tagged corpus.

            Results:
            Get some wrong tagging. Need manually get rid of them.
            The following are the wrong tags:
                I-2	3
                I-EN2	3
                I-E还	1
                I-N2…	1
                I-N2点	1
                I-PP2	1
                I-V	14
                I-[2	1
                I-快	1
            So we use a regex to find the wrong tags.
                ((2 )|(EN2)|(E还)|(N2…)|(N2点)|(PP2)|(V)|(\[2)|(快))
            """
        pattern = re.compile("\s+")

        tag_root_filepath = os.path.normpath(os.path.join(root_filepath, "f_hmm/tag/"))

        # list all the tagged corpus file
        with open(runout_filepath, "w", encoding="utf-8") as train_f:
            for filepath in os.listdir(tag_root_filepath):
                sentences = []
                with open(os.path.join(tag_root_filepath, filepath), encoding="utf-8") as tagged_f:
                    # firstly, get the whole sentence
                    sentence = ""
                    for line in tagged_f:
                        if line != "\n":
                            sentence += "%s\t" % line.strip()
                        else:
                            if sentence != "":
                                sentences.append(sentence)
                            sentence = ""

                # parse each sentence and get the word and the tag

                for sentence in sentences:
                    splits = pattern.split(sentence.strip())
                    words = []
                    tags = []
                    for a_split in splits:
                        if "/" in a_split:
                            results = a_split.split("/")
                            word = results[0]
                            tag = results[1]
                            words.append(word)
                            tags.append(tag)

                    seq_tag = False
                    final_pos = -1
                    for i in range(len(words)):
                        if not seq_tag:
                            if tags[i] == "":
                                train_f.write("%s/%s\t" % (words[i], "OT"))
                            else:
                                final_pos = HMMCorpus._find_final_position(tags, tags[i], i)
                                if final_pos != i:
                                    train_f.write("%s/%s\t" % (words[i], "B-" + tags[i]))
                                    seq_tag = True
                                else:
                                    train_f.write("%s/%s\t" % (words[i], "I-" + tags[i]))
                        else:
                            if i == final_pos:
                                train_f.write("%s/%s\t" % (words[i], "E-" + tags[i]))
                                seq_tag = False
                            else:
                                train_f.write("%s/%s\t" % (words[i], "M-" + tags[i]))

                    # write a nwe line
                    train_f.write("\n")

    @staticmethod
    def get_tagged_corpus(corpus_filepath):
        tag_root_filepath = os.path.normpath(os.path.join(root_filepath, "f_hmm/tag/"))

        with open(corpus_filepath, "w", encoding='utf-8') as writef:
            for file in os.listdir(tag_root_filepath):
                # get all lines
                with open(os.path.join(tag_root_filepath, file), encoding="utf-8") as readf:
                    lines = [line.strip() for line in readf.readlines()]

                # analyse each line
                line_no = 0
                runout = ""
                while line_no < len(lines):
                    if lines[line_no] == "" and runout:
                        writef.write("%s\n" % runout.strip())
                        runout = ""

                    elif lines[line_no]:
                        # get words and tags
                        splits = re_space_split.split(lines[line_no])
                        words, tags = [], []
                        for a_split in splits:
                            if "/" in a_split:
                                word, tag = a_split.split("/")
                                words.append(word)
                                tags.append(tag)

                        seq_tag = False
                        final_pos = -1
                        for i in range(len(words)):
                            if not seq_tag:
                                if tags[i] == "":
                                    runout += "%s/%s\t" % (words[i], "OT")
                                else:
                                    final_pos = HMMCorpus._find_final_position(tags, tags[i], i)
                                    if final_pos != i:
                                        runout += "%s/%s\t" % (words[i], "B-" + tags[i])
                                        seq_tag = True
                                    else:
                                        runout += "%s/%s\t" % (words[i], "I-" + tags[i])
                            else:
                                if i == final_pos:
                                    runout += "%s/%s\t" % (words[i], "E-" + tags[i])
                                    seq_tag = False
                                else:
                                    runout += "%s/%s\t" % (words[i], "M-" + tags[i])

                        if runout and not re_han.match(words[-1]):
                            writef.write("%s\n" % runout.strip())
                            runout = ""

                    line_no += 1

    @staticmethod
    def get_to_tag_corpus(start=0, end=500):
        """
        Get the corpus to tag
        :param start: the start line number to get into the tag files
        :param end: the end line number to get into the tag files
        """
        assert end > start >= 0
        gap = 10

        origin_filepath = ["D:\\My Data\\NLP\\SA\\waimai\\negative_corpus_v2.txt",
                           "D:\\My Data\\NLP\\SA\\waimai\\positive_corpus_v2.txt"]

        output_filepath = [os.path.normpath(os.path.join(root_filepath, "f_hmm/tag/negative_tag_corpus-%d.txt")),
                           os.path.normpath(os.path.join(root_filepath, "f_hmm/tag/positive_tag_corpus-%d.txt"))]

        for i in range(2):
            with open(origin_filepath[i], encoding="utf-") as readf:
                read_line_no = 0
                for line in readf:
                    if read_line_no >= start:
                        pass

                    # get the clauses
                    clauses = HMMCorpus.sentence2clauses(line)

                    # write the clause's segments
                    with open(output_filepath[i] % ((read_line_no - start) // gap), "a", encoding="utf-8") as writef:
                        for clause in clauses:
                            segments = seg.cut(clause)
                            writef.write("%s\n" % "\t".join([segment + "/" for segment in segments]))
                        writef.write("\n" * 2)

                    read_line_no += 1
                    if read_line_no == end:
                        break

    @staticmethod
    def sentence2clauses(sentence):
        return re_punctuation_split.findall(sentence.strip())

    @staticmethod
    def test_segments(start=0, end=1000):
        origin_filepath = ["D:\\My Data\\NLP\\SA\\waimai\\negative_corpus_v2.txt",
                           "D:\\My Data\\NLP\\SA\\waimai\\positive_corpus_v2.txt"]

        with open("f_seg/segments.txt", "w", encoding="utf-8") as writef:
            with open(origin_filepath[0], encoding="utf-8") as readf1:
                with open(origin_filepath[1], encoding="utf-8") as readf2:
                    i = 0
                    while True:
                        if i >= start:
                            line = readf1.readline()
                            clauses = HMMCorpus.sentence2clauses(line)
                            for clause in clauses:
                                segments = list(seg.cut(clause))
                                writef.write("%s\n" % segments)
                            writef.write("\n" * 2)

                            line = readf2.readline()
                            clauses = HMMCorpus.sentence2clauses(line)
                            for clause in clauses:
                                segments = list(seg.cut(clause))
                                writef.write("%s\n" % segments)
                            writef.write("\n" * 2)

                            i += 1

                            if i == end:
                                break


class BootstrappingHmm:
    def __init__(self):
        # the import parameters
        self.__tags = {}
        self.__init_prob = {}
        self.__emit_prob = {}
        self.__transition_prob = {}

        # the filepath parameters
        self.__infinitesimal = 1e-100

    def train(self, filepath):
        print("I'm training ...")

        # declare some variables
        tags_num = {}  # record the number of each tag
        init_num = {}  # record the number of the initial number
        transition_num = {}  # record the number of the transition numbers between tags
        emit_num = {}  # record the number of the the emit numbers between word and tag

        # the pattern for split
        pattern = re.compile("\s+")

        # open the file, read each line one by one
        with open(filepath, encoding="utf-8") as f:
            for line in f:
                # split the line into the several splits
                splits = pattern.split(line.strip())

                # establish two lists to record the word and the tag
                line_words = []
                # line_poses = []
                line_tags = []

                for a_split in splits:
                    # split every previous split into word and tag
                    results = a_split.split("/")
                    line_words.append(results[0])
                    # line_poses.append(results[1])
                    line_tags.append(results[-1])

                # get the length of two lists
                length = len(line_words)
                assert length == len(line_tags)

                # count the number of init, emit and transition

                # count the init
                tag = line_tags[0]
                init_num[tag] = init_num.get(tag, 0) + 1

                # count the transition
                for i in range(length - 1):
                    tag1 = line_tags[i]
                    tag2 = line_tags[i + 1]
                    if tag1 not in transition_num:
                        transition_num[tag1] = {}
                    transition_num[tag1][tag2] = transition_num[tag1].get(tag2, 0) + 1

                # count the emit and tag's number
                for i in range(length):
                    tag = line_tags[i]
                    word = line_words[i]
                    if tag not in emit_num:
                        emit_num[tag] = {}
                    emit_num[tag][word] = emit_num[tag].get(word, 0) + 1
                    tags_num[tag] = tags_num.get(tag, 0) + 1

        # count the probability of the self.init_prob, self.emit_prob, self.transition_prob
        # and write them into the file

        # write the tag num
        self.__tags = tags_num

        # write the init probability
        total = sum(init_num.values())
        for tag, num in sorted(init_num.items()):
            prob = num / total
            self.__init_prob[tag] = prob

        # write the transition probability
        # get the tag and the transition tag
        for tag1 in sorted(transition_num.keys()):
            tag_dict = transition_num[tag1]
            total = sum(tag_dict.values())
            self.__transition_prob[tag1] = {}
            for tag2 in sorted(tag_dict.keys()):
                num = tag_dict[tag2]
                prob = num / total
                self.__transition_prob[tag1][tag2] = prob
        for key in self.__tags:
            if key not in self.__transition_prob:
                self.__transition_prob[key] = {}

        # write the emit probability
        for tag in sorted(emit_num.keys()):
            tag_dict = emit_num[tag]
            total = sum(tag_dict.values())
            self.__emit_prob[tag] = {}
            for word in sorted(tag_dict.keys()):
                num = tag_dict[word]
                prob = num / total
                self.__emit_prob[tag][word] = prob
        for key in self.__tags:
            if key not in self.__emit_prob:
                self.__emit_prob[key] = {}

        print("Trains over ...")

    def __viterbi(self, observation):
        # record the first path and first probability
        prob_a = {}
        path_a = {}

        # initialize
        for tag in self.__tags.keys():
            path_a[tag] = [tag]
            prob_a[tag] = math.log(self.__init_prob.get(tag, self.__infinitesimal)) + \
                math.log(self.__emit_prob[tag].get(observation[0], self.__infinitesimal))

        # traversal the observation
        for i in range(1, len(observation)):
            # copy the previous prob and path
            # and initialize the new prob and path
            prob_b = prob_a
            path_b = path_a

            path_a = {}
            prob_a = {}

            # get the previous max prob and corresponding tag
            for tag in self.__tags.keys():
                max_prob, pre_tag = max(
                    [(pre_prob + math.log(self.__transition_prob[pre_tag].get(tag, self.__infinitesimal)) +
                      math.log(self.__emit_prob[tag].get(observation[i], self.__infinitesimal)), pre_tag)
                     for pre_tag, pre_prob in prob_b.items()])

                prob_a[tag] = max_prob
                path_a[tag] = path_b[pre_tag] + [tag]

        final_tag, final_prob = max(prob_a.items(), key=lambda a_item: a_item[1])
        return path_a[final_tag]

    def tag(self, sequence, tag_only=False):
        """
        This is viterbi algorithm
        """
        # judge whether the sequence is a list
        if not isinstance(sequence, list):
            raise ValueError("Error. Not word list.")
        elif tag_only:
            return self.__viterbi(sequence)
        else:
            return list(zip(sequence, self.__viterbi(sequence)))


class BootstrappingMaster:
    """BootstrappingMaster"""
    def __init__(self, train_corpus_filepath):
        self.hmm1 = BootstrappingHmm()
        self.hmm2 = BootstrappingHmm()

        self.train_corpus_filepath = train_corpus_filepath
        self.bootstrapping_corpus_filepath = "f_hmm/hmm_bootstrapping_corpus.txt"
        self.hmm1_filepath = "f_hmm/hmm1_corpus.txt"
        self.hmm2_filepath = "f_hmm/hmm2_corpus.txt"

        self.bootstrap_contents = []
        self.added = False
        self.split_pattern = re.compile("\s+")
        self.load_bootstrap()

    def load_bootstrap(self):
        with open(self.bootstrapping_corpus_filepath, encoding="utf-8") as bootstrap_f:
            for line in bootstrap_f:
                self.bootstrap_contents.append(line.strip())

    @staticmethod
    def check_filepath(filepath):
        if os.path.exists(filepath):
            return True
        else:
            return False

    def distribute(self):
        """Distribute the tagged corpus."""
        if self.check_filepath(self.train_corpus_filepath):
            print("Distributing.")

            hmm1_file = open(self.hmm1_filepath, "w", encoding="utf-8")
            hmm2_file = open(self.hmm2_filepath, "w", encoding="utf-8")

            with open(self.train_corpus_filepath, encoding="utf-8") as f:
                contents = f.readlines()
            index_list = list(range(len(contents)))

            turn = 0

            while len(index_list) > 0:
                index = choice(index_list)
                index_list.remove(index)
                if turn == 0:
                    hmm1_file.write("%s" % contents[index])
                    turn += 1
                else:
                    hmm2_file.write("%s" % contents[index])
                    turn = 0

            hmm1_file.close()
            hmm2_file.close()
        else:
            print("Please check. Can not find the corpus path.")

    def bootstrapping(self):
        while True:
            # randomly get the train corpus and distribute to each hmm file
            self.distribute()
            # train each hmm
            self.hmm1.train(self.hmm1_filepath)
            self.hmm2.train(self.hmm2_filepath)

            # tag each test corpus
            # if two tags are equal, then add it into corpus file, and change the state of self.added
            with open(self.train_corpus_filepath, 'a', encoding="utf-8") as train_f:
                for line in self.bootstrap_contents:
                    hmm1_tags = []
                    hmm2_tags = []
                    clauses = []
                    for clause in HMMCorpus.sentence2clauses(line.strip()):
                        segments = seg.cut(clause)
                        clauses.append(segments)
                        hmm1_tags.append(self.hmm1.tag(segments, tag_only=True))
                        hmm2_tags.append(self.hmm2.tag(segments, tag_only=True))

                    if hmm1_tags == hmm2_tags:
                        self.added = True
                        print("Add a new data.")
                        runout = ""
                        for i in range(len(hmm1_tags)):
                            content = ""
                            for j in range(len(hmm1_tags[i])):
                                content += "%s/%s\t" % (clauses[i][j], hmm1_tags[i][j])
                            runout += "%s\n" % content.strip()
                        train_f.write("%s\n" % runout.strip())
                        self.bootstrap_contents.remove(line)

            print("Length of remaining corpus: %d" % len(self.bootstrap_contents))
            # check whether there are new data added
            if not self.added:
                break
            else:
                # change the sate of self.added
                self.added = False


def _test1():
    """
    Get the tag corpus
    """
    HMMCorpus.get_to_tag_corpus()


def _test2():
    """
    Test segment waimai corpus
    """
    start = 0
    end = 1000
    HMMCorpus.test_segments(start, end)


def _test3():
    """
    From the tag files correct the tag corpus,
    and Using Bootstrapping method to get more tag corpus.
    """
    corpus_filepath = "f_hmm/hmm_train_corpus.txt"
    HMMCorpus.get_tagged_corpus(corpus_filepath)
    # master = BootstrappingMaster(corpus_filepath)
    # master.bootstrapping()


if __name__ == "__main__":
    pass
    # _test1()
    # _test2()
    _test3()
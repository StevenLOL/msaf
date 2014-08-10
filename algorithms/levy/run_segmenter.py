#!/usr/bin/env python
'''Runs the Levy segmenter for boundaries across the Segmentation dataset

'''

__author__ = "Oriol Nieto"
__copyright__ = "Copyright 2014, Music and Audio Research Lab (MARL)"
__license__ = "GPL"
__version__ = "1.0"
__email__ = "oriol@nyu.edu"

import sys
import glob
import os
import argparse
import time
import logging
import jams2
import json
import subprocess
from joblib import Parallel, delayed

import sys
sys.path.append("../../")
import msaf_io as MSAF


def process_track(jam_file, feat_file, annot_beats, feature, annot_bounds):
    """Processes one single track."""

    # Only analize files with annotated beats
    if annot_beats:
        jam = jams2.load(jam_file)
        if jam.beats == []:
            return
        if jam.beats[0].data == []:
            return

    if annot_beats:
        annot_beats_str = "1"
    else:
        annot_beats_str = "0"
    if annot_bounds:
        # write down the annotated boundary indeces to "annot_bounds.txt"
        audio_file  = feat_file.replace("features", "audio")[:-5] + ".mp3"
        chroma, mfcc, beats, dur = MSAF.get_features(
            audio_file, annot_beats=annot_beats)
        bounds_dict = {}
        try:
            bounds_dict["bounds"] = list(
                MSAF.read_annot_bound_frames(audio_file, beats))
        except:
            logging.warning("Could not find annotated boundaries in %s" %
                            jam_file)
            return
        with open("annot_bounds.json", "w") as f:
            json.dump(bounds_dict, f)
        annot_bounds_str = "1"
    else:
        annot_bounds_str = "0"

    logging.info("Segmenting %s" % feat_file)

    # Levy segmenter call
    cmd = ["./segmenter", feat_file.replace(" ", "\ ").replace("&", "\&").
           replace("'", "\\'").replace("(", "\(").replace(")", "\)"),
           annot_beats_str, feature, annot_bounds_str]
    print " ".join(cmd)

    # Shell is needed for files with spaces
    subprocess.call(" ".join(cmd), shell=True)


def process(in_path, annot_beats=False, feature="mfcc", annot_bounds=False,
            ds_name="*", n_jobs=4):
    """Main process."""

    # Get relevant files
    feat_files = glob.glob(os.path.join(in_path, "features",
                                        "%s_*.json" % ds_name))
    jam_files = glob.glob(os.path.join(in_path, "annotations",
                                       "%s_*.jams" % ds_name))

    # Run segmenter in parallel
    Parallel(n_jobs=n_jobs)(delayed(process_track)(
        jam_file, feat_file, annot_beats, feature, annot_bounds)
        for feat_file, jam_file in zip(feat_files, jam_files))


def main():
    """Main function to parse the arguments and call the main process."""
    parser = argparse.ArgumentParser(description=
        "Runs the Levy segmenter across a the Segmentation dataset and "
        "stores the results in the estimations folder",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("in_path",
                        action="store",
                        help="Input dataset")
    parser.add_argument("feature",
                        action="store",
                        default="mfcc",
                        help="Feature to be used (mfcc, hpcp or tonnetz)")
    parser.add_argument("-b",
                        action="store_true",
                        dest="annot_beats",
                        help="Use annotated beats",
                        default=False)
    parser.add_argument("-bo",
                        action="store_true",
                        dest="annot_bounds",
                        help="Use annotated bounds",
                        default=False)
    parser.add_argument("-d",
                        action="store",
                        dest="ds_name",
                        default="*",
                        help="The prefix of the dataset to use "
                        "(e.g. Isophonics, SALAMI")
    parser.add_argument("-j",
                        action="store",
                        dest="n_jobs",
                        default=4,
                        type=int,
                        help="The number of processes to run in parallel")
    args = parser.parse_args()
    start_time = time.time()

    # Setup the logger
    logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s',
        level=logging.INFO)

    # Run the algorithm
    process(args.in_path, annot_beats=args.annot_beats, n_jobs=args.n_jobs,
            feature=args.feature, annot_bounds=args.annot_bounds,
            ds_name=args.ds_name)

    # Done!
    logging.info("Done! Took %.2f seconds." % (time.time() - start_time))


if __name__ == '__main__':
    main()

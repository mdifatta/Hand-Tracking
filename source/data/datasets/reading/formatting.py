import numpy as np
from data.naming import IN, OUT
from data.datasets.reading.exceptions import SkipFrameException
from library.hand_vector_field.field_builder import build_hand_fields

# Here are specified pre-stored formats used in different context
# The present file contains:
#   0) an extensive description of the formatting object specification
#   1) functions to manipulate existing high-level formats easily
#   2) data-reading low level format specifications
#   3) cross-data aggregation into mid-level data specifications
#   4) dataset-organization high level format specifications
#

# ######################## SECTION 0: FORMAT SPECIFICATIONS #######################
#
#
#       LOW LEVEL SPECIFICATION:
#               (name, consumer):
#                   name: when a .mat is read, we want to refer to its 'name' field
#                   consumer: the raw content of the 'name' field of the .mat must pass
#                             through this function before it is served.
#                             usage example: normalize, dequantize, decompress, expand info
#       MID LEVEL SPECIFICATION:
#               (low1, low2, low3...):
#                   process each low-level spec independently and return a single content
#                   which is the concatenation of the returned contents along the last axis.
#                   Equivalent to np.concatenate((low1content, low2content, ...), axis=-1)
#                   Useful to overlap different data formats like RGB + D in RGBD
#                   This layer may be extended in the future to allow more complex operations if needed
#       HIGH LEVEL SPECIFICATION:
#               {
#                   key1: midlevel1,
#                   key2: midlevel2,
#                   key3: midlevel3,
#                   ...
#               }
#                   specify that the final dataset provided will have to be organized as a dictionary
#                   with the given keys, to each key corresponding a batch read according to
#                   the mid-level specification provided.
#                   NOTICE: for compatibility with training functions, it is necessary to use as keys
#                           the names generated by IN and OUT NameGenerators in data.naming.py corresponding
#                           to the same inputs and outputs with the same names as declared in the model
#                           description
#
#
#       As examples see the next sections with already prepared specifications
#
# ######################### SECTION 1: MANIPULATION #####################

# these functions allow to change low level format specs in high level format dicts


def format_set_field_name(name, format, entry, channel_index=0):
    """
    Set the .mat field name of a particular component of a format dict
    :param name: the .mat field name to insert
    :param format: the high level format dict to manipulate
    :param entry: the high level entry to be modified
    :param channel_index: the channel order where the .mat content to redirect is stored
    :return: the modified format
    """
    format[entry][channel_index] = [name, format[entry][channel_index][1]]
    return format


def format_add_inner_func(f, format, entry, channel_index=0):
    """
    Add a consumer function directly on the .mat output of a particular component of a format dict
    :param f: the consumer function to be pipelined
    :param format: the high level format dict to manipulate
    :param entry: the high level entry to be modified
    :param channel_index: the channel order where the .mat content to redirect is stored
    :return: the modified format
    """
    old_f = format[entry][channel_index][1]
    format[entry][channel_index] = [format[entry][channel_index][0], lambda x: old_f(f(x))]
    return format


def format_add_outer_func(f, format, entry, channel_index=0):
    """
    Add a consumer function at the end of the consumer pipeline of a particular component of a format dict
    :param f: the consumer function to be pipelined
    :param format: the high level format dict to manipulate
    :param entry: the high level entry to be modified
    :param channel_index: the channel order where the .mat content to redirect is stored
    :return: the modified format
    """
    old_f = format[entry][channel_index][1]
    format[entry][channel_index] = [format[entry][channel_index][0], lambda x: f(old_f(x))]
    return format

# ######################### SECTION 2: LOW-LEVEL STANDARDS #####################

# PLEASE USE LISTS, NOT TUPLES, TO ALLOW RUNTIME MODIFICATIONS

# LOWFMT_USE_FIELD = [NAME, CONSUMER]


LOWFMT_CROP_IMG = ['frame', lambda x: x / 255.0]
LOWFMT_CROP_HEATMAP = ['heatmap', lambda x: np.expand_dims(x / 255.0, axis=-1)]
LOWFMT_CROP_DEPTH = ['depth', lambda x: np.expand_dims(x, axis=-1)]

LOWFMT_JUNC_IMG = ['cut', lambda x: x / 255.0]
LOWFMT_JUNC_HEATMAP = ['heatmap_array', lambda x: x / 255.0]
LOWFMT_JUNC_VISIBILITY = ['visible', lambda x: x[:, 0]]
LOWFMT_JUNC_VEC_FIELD = ['heatmap_array', lambda x: build_hand_fields(x / 255.0)]

LOWFMT_PB_IMG = ['cut', lambda x: x / 255.0]
LOWFMT_PB_LABEL = ['pb', lambda x: x[0]]
LOWFMT_PB_CONF = ['conf', lambda x: x[0]]

# ######################### SECTION 3: MID-LEVEL STANDARDS #####################

# PLEASE USE LISTS, NOT TUPLES, TO ALLOW RUNTIME MODIFICATIONS

# MIDFMT_USE_FIELD = [LOW1, LOW2, ..., LOWN]

MIDFMT_CROP_RGB = [LOWFMT_CROP_IMG]
MIDFMT_CROP_RGBD = [LOWFMT_CROP_IMG, LOWFMT_CROP_DEPTH]
MIDFMT_CROP_HEATMAP = [LOWFMT_CROP_HEATMAP]

MIDFMT_JUNC_RGB = [LOWFMT_JUNC_IMG]
MIDFMT_JUNC_HEATMAP = [LOWFMT_JUNC_HEATMAP]
MIDFMT_JUNC_VISIBILITY = [LOWFMT_JUNC_VISIBILITY]
MIDFMT_JUNC_VEC_FIELD = [LOWFMT_JUNC_VEC_FIELD]

MIDFMT_PB_IMG = [LOWFMT_PB_IMG]
MIDFMT_PB_LABEL = [LOWFMT_PB_LABEL]
MIDFMT_PB_CONF = [LOWFMT_PB_CONF]

# ######################### SECTION 4: HIGH-LEVEL STANDARDS #####################

CROPS_STD_FORMAT = {
    IN(0): MIDFMT_CROP_RGB,
    OUT(0): MIDFMT_CROP_HEATMAP
}

CROPS_STD_DEPTH_FORMAT = {
    IN(0): MIDFMT_CROP_RGBD,
    OUT(0): MIDFMT_CROP_HEATMAP
}

JUNC_STD_FORMAT = {
    IN(0): MIDFMT_JUNC_RGB,
    OUT(0): MIDFMT_JUNC_HEATMAP,
    OUT(1): MIDFMT_JUNC_VISIBILITY
}

JUNC_VECFIELD_STD_FORMAT = {
    IN('img'): MIDFMT_JUNC_RGB,
    OUT('heat'): MIDFMT_JUNC_HEATMAP,
    OUT('vis'): MIDFMT_JUNC_VISIBILITY,
    OUT('field'): MIDFMT_JUNC_VEC_FIELD
}

PB_STD_FORMAT = {
    IN(0): MIDFMT_PB_IMG,
    OUT(0): MIDFMT_PB_LABEL,
    OUT('conf'): MIDFMT_PB_CONF
}


def confidence_filtered_pb_format(min_confidence):
    def check_minconf(x):
        if x < min_confidence:
            raise SkipFrameException
        return x

    return format_add_outer_func(f=check_minconf,
                                 entry=OUT('conf'),
                                 format=PB_STD_FORMAT)

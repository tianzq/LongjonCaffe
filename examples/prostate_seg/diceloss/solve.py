from __future__ import division

import os
import sys
CAFFE_ROOT = "/the/path/to/your/longjoncaffe/caffe_FCN/"
#CAFFE_ROOT = "/home/ztian5/Deep_Learning/Caffe_3D/3D-Caffe-master-CuDNN/"
caffe_path = os.path.join(CAFFE_ROOT, "python")
if caffe_path not in sys.path:
	sys.path.insert(0, caffe_path)
import caffe
import numpy as np

import pdb
import matplotlib.pyplot as plt

# make a bilinear interpolation kernel
# credit @longjon
def upsample_filt(size):
    factor = (size + 1) // 2
    if size % 2 == 1:
        center = factor - 1
    else:
        center = factor - 0.5
    og = np.ogrid[:size, :size]
    return (1 - abs(og[0] - center) / factor) * \
           (1 - abs(og[1] - center) / factor)

# set parameters s.t. deconvolutional layers compute bilinear interpolation
# N.B. this is for deconvolution without groups
def interp_surgery(net, layers):
    for l in layers:
        m, k, h, w = net.params[l][0].data.shape
        if m != k:
            print 'input + output channels need to be the same'
            raise
        if h != w:
            print 'filters need to be square'
            raise
        filt = upsample_filt(h)
        net.params[l][0].data[range(m), range(k), :, :] = filt

# base net -- the learned coarser model
base_weights = 'fcn-32s-pascalcontext.caffemodel'

# init
caffe.set_mode_gpu()
caffe.set_device(0)
# caffe.set_mode_cpu()

solver = caffe.SGDSolver('solver.prototxt')

# do net surgery to set the deconvolution weights for bilinear interpolation
interp_layers = [k for k in solver.net.params.keys() if 'up' in k]
interp_surgery(solver.net, interp_layers)

# copy base weights for fine-tuning
solver.net.copy_from(base_weights)

# solve straight through -- a better approach is to define a solving loop to
# 1. take SGD steps
# 2. score the model by the test net `solver.test_nets[0]`
# 3. repeat until satisfied

for ii in range(0,5000):
    solver.step(1)

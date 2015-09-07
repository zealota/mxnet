# pylint: skip-file
import numpy as np
import mxnet as mx
import copy
"""
CXXNET Result:
step1: wmat_lr = 0.05, bias_lr = 0.1, mom = 0.9
[1] train-error:0.452865  val-error:0.3614
[2] train-error:0.280231  val-error:0.2504
[3] train-error:0.220968  val-error:0.2456
[4] train-error:0.18746 val-error:0.2145
[5] train-error:0.165221  val-error:0.1796
[6] train-error:0.150056  val-error:0.1786
[7] train-error:0.134571  val-error:0.157
[8] train-error:0.122582  val-error:0.1429
[9] train-error:0.113891  val-error:0.1398
[10]  train-error:0.106458  val-error:0.1469
[11]  train-error:0.0985054 val-error:0.1447
[12]  train-error:0.0953684 val-error:0.1494
[13]  train-error:0.0872962 val-error:0.1311
[14]  train-error:0.0832401 val-error:0.1544
[15]  train-error:0.0773857 val-error:0.1268
[16]  train-error:0.0743087 val-error:0.125
[17]  train-error:0.0714114 val-error:0.1189
[18]  train-error:0.066616  val-error:0.1424
[19]  train-error:0.0651175 val-error:0.1322
[20]  train-error:0.0616808 val-error:0.111
step2: lr = 0.01, bias_lr = 0.02, mom = 0.9
[21]  train-error:0.033368  val-error:0.0907
[22]  train-error:0.0250959 val-error:0.0876
[23]  train-error:0.0220388 val-error:0.0867
[24]  train-error:0.0195812 val-error:0.0848
[25]  train-error:0.0173833 val-error:0.0872
[26]  train-error:0.0154052 val-error:0.0878
[27]  train-error:0.0141264 val-error:0.0863
[28]  train-error:0.0134071 val-error:0.0865
[29]  train-error:0.0116688 val-error:0.0878
[30]  train-error:0.0106298 val-error:0.0873
step3: lr = 0.001, bias_lr = 0.002, mom = 0.9
[31]  train-error:-nan  val-error:0.0873
[31]  train-error:0.0067735 val-error:0.0859
[32]  train-error:0.0049952 val-error:0.0835
[33]  train-error:0.00485534  val-error:0.0849
[34]  train-error:0.00367647  val-error:0.0839
[35]  train-error:0.0034367 val-error:0.0844
[36]  train-error:0.00275735  val-error:0.084
[37]  train-error:0.00221787  val-error:0.083
[38]  train-error:0.00171835  val-error:0.0838
[39]  train-error:0.00125879  val-error:0.0833
[40]  train-error:0.000699329 val-error:0.0842
"""

np.random.seed(1812)

conv_cnt = 1
concat_cnt = 1
pool_cnt = 1

def ConvFactory(**kwargs):
    global conv_cnt
    param = copy.copy(kwargs)
    act = param["act_type"]
    del param["act_type"]
    param["name"] = "conv%d" % conv_cnt
    conv = mx.symbol.Convolution(**param)
    bn = mx.symbol.BatchNorm(data = conv, name="bn%d" % conv_cnt)
    relu = mx.symbol.Activation(data = bn, name = "%s%d" % (act, conv_cnt), act_type=act)
    conv_cnt += 1
    return relu


def DownsampleFactory(data, ch_3x3, stride = 2):
    global pool_cnt
    global concat_cnt
    param = {}
    # conv 3x3
    param["kernel"] = (3, 3)
    param["stride"] = (stride, stride)
    param["num_filter"] = ch_3x3
    param["act_type"] = "relu"
    param["data"] = data
    param["nstep"] = 100
    param["pad"] = (1, 1)
    conv3x3 = ConvFactory(**param)
    # pool
    del param["num_filter"]
    del param["act_type"]
    del param["nstep"]
    del param["pad"]
    param["pool_type"] = "max"
    param["name"] = "pool%d" % pool_cnt
    pool = mx.symbol.Pooling(**param)
    pool_cnt += 1
    # concat
    concat = mx.symbol.Concat(*[conv3x3, pool], name="concat%d" % concat_cnt)
    concat_cnt += 1
    return concat

def SimpleFactory(data, ch_1x1, ch_3x3):
    global concat_cnt
    param = {}
    # 1x1
    param["kernel"] = (1, 1)
    param["num_filter"] = ch_1x1
    param["pad"] = (0, 0)
    param["stride"] = (1, 1)
    param["act_type"] = "relu"
    param["data"] = data
    param["nstep"] = 100
    conv1x1 = ConvFactory(**param)

    # 3x3
    param["kernel"] = (3, 3)
    param["num_filter"] = ch_3x3
    param["pad"] = (1, 1)
    conv3x3 = ConvFactory(**param)

    #concat
    concat = mx.symbol.Concat(*[conv1x1, conv3x3], name="concat%d" % concat_cnt)
    concat_cnt += 1
    return concat

def RandomInit(narray):
    in_num = narray.numpy.shape[1]
    out_num = narray.numpy.shape[0]
    a = np.sqrt(3.0 / (in_num + out_num))
    tmp = mx.narray.create((narray.numpy.shape))
    tmp.numpy[:] = np.random.uniform(-a, a, narray.numpy.shape)
    tmp.copyto(narray)

data = mx.symbol.Variable(name="data")
conv1 = ConvFactory(data=data, kernel=(3,3), pad=(1,1), num_filter=96, act_type="relu")
in3a = SimpleFactory(conv1, 32, 32)
in3b = SimpleFactory(in3a, 32, 48)
in3c = DownsampleFactory(in3b, 80)
in4a = SimpleFactory(in3c, 112, 38)
in4b = SimpleFactory(in4a, 96, 64)
in4c = SimpleFactory(in4b, 80, 80)
in4d = SimpleFactory(in4c, 48, 96)
in4e = DownsampleFactory(in4d, 96)
in5a = SimpleFactory(in4e, 176, 160)
in5b = SimpleFactory(in5a, 176, 160)
pool = mx.symbol.Pooling(data=in5b, pool_type="avg", kernel=(7,7), name="pool%d" % pool_cnt)
flatten = mx.symbol.Flatten(data=pool, name="flatten1")
fc = mx.symbol.FullyConnected(data=flatten, num_hidden=10, name="fc1")
loss = mx.symbol.Softmax(data=fc, name="softmax")
args_list = loss.list_arguments()

data_shape = (128, 3, 28, 28)
arg_shapes, out_shapes, aux_shapes = loss.infer_shape(data=data_shape)

arg_narrays = [mx.narray.create(shape, ctx=mx.Context("gpu")) for shape in arg_shapes]
grad_narrays = [mx.narray.create(shape, ctx=mx.Context("gpu")) for shape in arg_shapes]

inputs = dict(zip(args_list, arg_narrays))

name2shape = dict(zip(args_list, arg_shapes))
pred = mx.narray.create(out_shapes[0])

np.random.seed(0)
# set random weight
for name, narray in inputs.items():
    if "weight" in name:
        tmp = mx.narray.create(name2shape[name])
        tmp.numpy[:] = np.random.uniform(-0.07, 0.07, name2shape[name])
        tmp.copyto(narray)
    if "bias" in name:
        narray[:] = 0.0

# bind executer
# TODO(bing): think of a better bind interface
executor = loss.bind(mx.Context('gpu'), arg_narrays, grad_narrays)
# update

out_narray = executor.heads()[0]
grad_narray = mx.narray.create(out_narray.shape)

epoch = 9
lr = 0.1
wd = 0.0004

def Update(grad, weight):
    weight[:] -= lr * grad  / batch_size

block = list(zip(grad_narrays, arg_narrays))

#check data
get_data.GetCifar10()
train_dataiter = mx.io.ImageRecordIter(
        path_imgrec="data/cifar/train.rec",
        mean_img="data/cifar/cifar_mean.bin",
        rand_crop=True,
        rand_mirror=True,
        input_shape=(3,28,28),
        batch_size=128,
        nthread=1)
test_dataiter = mx.io.ImageRecordIter(
        path_imgrec="data/cifar/test.rec",
        mean_img="data/cifar/cifar_mean.bin",
        rand_crop=True,
        rand_mirror=True,
        input_shape=(3,28,28),
        batch_size=100,
        nthread=1)

tmp_label = mx.narray.create(name2shape["sm_label"])

def test_cifar():
    acc_train = 0.
    acc_val = 0.
    for i in range(epoch):
        # train
        print("Epoch %d" % i)
        train_acc = 0.0
        val_acc = 0.0
        train_nbatch = 0
        val_nbatch = 0
        for data, label in train_dataiter:
            data = data
            tmp_label.numpy[:] = label.numpy.reshape(tmp_label.shape)
            data.copyto(inputs["data"])
            tmp_label.copyto(inputs["sm_label"])
            executor.forward()
            out_narray.copyto(pred)
            train_acc += CalAcc(pred.numpy, label.numpy.flatten())
            train_nbatch += 1
            out_narray.copyto(grad_narray)
            executor.backward([grad_narray])

            for grad, weight in block:
                Update(grad, weight)

        # evaluate
        for data, label in val_dataiter:
            data = data
            label = label.numpy.flatten()
            data.copyto(inputs["data"])
            executor.forward()
            out_narray.copyto(pred)
            val_acc += CalAcc(pred.numpy, label)
            val_nbatch += 1
        acc_train = train_acc / train_nbatch
        acc_val = val_acc / val_nbatch
        print("Train Acc: ", train_acc / train_nbatch)
        print("Valid Acc: ", val_acc / val_nbatch)
        train_dataiter.reset()
        val_dataiter.reset()
    assert(acc_train > 0.98)
    assert(acc_val > 0.97)

if __name__ == "__main__":
    test_cifar()
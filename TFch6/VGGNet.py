# -*- coding: utf-8 -*-#

"""
File         :      VGGNet.py
Description  :  
Author       :      赵金朋
Modify Time  :      2019/8/1 10:22
"""
from datetime import datetime
import math
import time
import tensorflow as tf
#tensor:多维向量
def conv_op(input_op, name, kh, kw, n_out, dh, dw, p):
    #参数详解：
    #input_op:输入的tensor;
    #name:这一层的名字
    #kh:卷积核的高
    #kw:卷积核的宽
    #n_out:卷积核数量，即输出通道数
    #dh:步长的高
    #dw:步长的宽
    #获取输入input_op的通道数
    n_in = input_op.get_shape()[-1].value

    with tf.name_scope(name) as scope:
        kernel = tf.get_variable(scope+"w",
                                 shape=[kh, kw, n_in, n_out],
                                 dtype=tf.float32,
                                 initializer=tf.contrib.layers.xavier_initializer_conv2d())
        #对input_op进行卷积处理
        conv = tf.nn.conv2d(input_op, kernel, (1, dh, dw, 1), padding='SAME')
        bias_init_val = tf.constant(0.0, shape=[n_out], dtype=tf.float32)
        #将bias转化成可训练的参数
        biases = tf.Variable(bias_init_val, trainable=True, name='b')
        #将卷积结果conv与bias相加
        z = tf.nn.bias_add(conv, biases)
        activation = tf.nn.relu(z, name=scope)
        #将创建卷积层是用到参数kernel和biases添加进参数列表
        p += [kernel, biases]
        #卷积层的输出
        return activation
#定义全连接层的创建函数
def fc_op(input_op, name, n_out, p):
    n_in = input_op.get_shape()[-1].value

    with tf.name_scope(name) as scope:
        kernel = tf.get_variable(scope+"w",
                                 shape=[n_in, n_out],
                                 dtype=tf.float32,
                                 initializer=tf.contrib.layers.xavier_initializer())
        biases = tf.Variable(tf.constant(0.1, shape=[n_out], dtype=tf.float32), name='b')
        #对输入变量input_op与kernel做矩阵乘法并加上biases
        activation = tf.nn.relu_layer(input_op, kernel, biases, name=scope)
        p += [kernel, biases]
        return activation

def mpool_op(input_op, name, kh, kw, dh, dw):
    return tf.nn.max_pool(input_op,
                          ksize=[1, kh, kw, 1],
                          strides=[1, dh, dw, 1],
                          padding='SAME',
                          name=name)

#创建网络
#keep_prob控制dropout比率的一个placeholder
def inference_op(input_op, keep_prob):
    #初始化参数列表
    p = []
    # 输入 224x224x3

    # block 1 -- 224*224*64--224*224*64-outputs 112x112x64
    conv1_1 = conv_op(input_op, name="conv1_1", kh=3, kw=3, n_out=64, dh=1, dw=1, p=p)
    conv1_2 = conv_op(conv1_1,  name="conv1_2", kh=3, kw=3, n_out=64, dh=1, dw=1, p=p)
    pool1 = mpool_op(conv1_2,   name="pool1",   kh=2, kw=2, dw=2, dh=2)

    # block 2 --112*112*128-112*112*128- outputs 56x56x128
    conv2_1 = conv_op(pool1,    name="conv2_1", kh=3, kw=3, n_out=128, dh=1, dw=1, p=p)
    conv2_2 = conv_op(conv2_1,  name="conv2_2", kh=3, kw=3, n_out=128, dh=1, dw=1, p=p)
    pool2 = mpool_op(conv2_2,   name="pool2",   kh=2, kw=2, dh=2, dw=2)

    # # block 3 --56*56*256-56*56*256-- outputs 28x28x256
    conv3_1 = conv_op(pool2,    name="conv3_1", kh=3, kw=3, n_out=256, dh=1, dw=1, p=p)
    conv3_2 = conv_op(conv3_1,  name="conv3_2", kh=3, kw=3, n_out=256, dh=1, dw=1, p=p)
    conv3_3 = conv_op(conv3_2,  name="conv3_3", kh=3, kw=3, n_out=256, dh=1, dw=1, p=p)
    pool3 = mpool_op(conv3_3,   name="pool3",   kh=2, kw=2, dh=2, dw=2)

    # block 4 -- 28*28*512--28*28-512--outputs 14x14x512
    conv4_1 = conv_op(pool3,    name="conv4_1", kh=3, kw=3, n_out=512, dh=1, dw=1, p=p)
    conv4_2 = conv_op(conv4_1,  name="conv4_2", kh=3, kw=3, n_out=512, dh=1, dw=1, p=p)
    conv4_3 = conv_op(conv4_2,  name="conv4_3", kh=3, kw=3, n_out=512, dh=1, dw=1, p=p)
    pool4 = mpool_op(conv4_3,   name="pool4",   kh=2, kw=2, dh=2, dw=2)

    # block 5 -- 14*14*512--14*14*512--outputs 7x7x512
    conv5_1 = conv_op(pool4,    name="conv5_1", kh=3, kw=3, n_out=512, dh=1, dw=1, p=p)
    conv5_2 = conv_op(conv5_1,  name="conv5_2", kh=3, kw=3, n_out=512, dh=1, dw=1, p=p)
    conv5_3 = conv_op(conv5_2,  name="conv5_3", kh=3, kw=3, n_out=512, dh=1, dw=1, p=p)
    pool5 = mpool_op(conv5_3,   name="pool5",   kh=2, kw=2, dw=2, dh=2)

    # flatten 对卷及网络的输出结果进行扁平化
    shp = pool5.get_shape()
    flattened_shape = shp[1].value * shp[2].value * shp[3].value
    #将每个样本化为长度为7x7x512=25088的一维向量
    resh1 = tf.reshape(pool5, [-1, flattened_shape], name="resh1")

    # fully connected4096个节点
    fc6 = fc_op(resh1, name="fc6", n_out=4096, p=p)
    fc6_drop = tf.nn.dropout(fc6, keep_prob, name="fc6_drop")

    fc7 = fc_op(fc6_drop, name="fc7", n_out=4096, p=p)
    fc7_drop = tf.nn.dropout(fc7, keep_prob, name="fc7_drop")

    fc8 = fc_op(fc7_drop, name="fc8", n_out=1000, p=p)
    softmax = tf.nn.softmax(fc8)
    predictions = tf.argmax(softmax, 1)
    return predictions, softmax, fc8, p

def time_tensorflow_run(session, target, feed, info_string):
    num_steps_burn_in = 10
    total_duration = 0.0
    total_duration_squared = 0.0
    for i in range(num_batches + num_steps_burn_in):
        start_time = time.time()
        _ = session.run(target, feed_dict=feed)
        duration = time.time() - start_time
        if i >= num_steps_burn_in:
            if not i % 10:
                print ('%s: step %d, duration = %.3f' %
                       (datetime.now(), i - num_steps_burn_in, duration))
            total_duration += duration
            total_duration_squared += duration * duration
    mn = total_duration / num_batches
    vr = total_duration_squared / num_batches - mn * mn
    sd = math.sqrt(vr)
    print ('%s: %s across %d steps, %.3f +/- %.3f sec / batch' %
           (datetime.now(), info_string, num_batches, mn, sd))

def run_benchmark():
    with tf.Graph().as_default():
        image_size = 224
        #首先生成尺寸为224*224的随机图片
        images = tf.Variable(tf.random_normal([batch_size,
                                               image_size,
                                               image_size, 3],
                                               dtype=tf.float32,
                                               stddev=1e-1))

        keep_prob = tf.placeholder(tf.float32)
        predictions, softmax, fc8, p = inference_op(images, keep_prob)

        init = tf.global_variables_initializer()

        config = tf.ConfigProto()
        config.gpu_options.allocator_type = 'BFC'
        sess = tf.Session(config=config)
        sess.run(init)

        time_tensorflow_run(sess, predictions, {keep_prob:1.0}, "Forward")
        #最后的全连接层的输出fc8的12loss
        objective = tf.nn.l2_loss(fc8)
        grad = tf.gradients(objective, p)
        time_tensorflow_run(sess, grad, {keep_prob:0.5}, "Forward-backward")

batch_size=10
num_batches=100
run_benchmark()

"""
Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License").
You may not use this file except in compliance with the License.
A copy of the License is located at

http://www.apache.org/licenses/LICENSE-2.0

or in the "license" file accompanying this file. This file is distributed
on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
express or implied. See the License for the specific language governing
permissions and limitations under the License.
"""

from tqdm import tqdm

import torch
from torch.autograd import Variable
from utils import map_label_to_target


class Trainer(object):
    """"""

    def __init__(self, args, model, criterion, optimizer):
        """"""
        self.args = args
        self.model = model
        self.criterion = criterion
        self.optimizer = optimizer
        self.epoch = 0

    def train(self, dataset):
        """"""
        self.model.train()
        self.optimizer.zero_grad()

        total_loss = 0.0
        indices = torch.randperm(len(dataset))

        for idx in tqdm(range(len(dataset)), desc='Training epoch ' + str(self.epoch + 1) + ''):
            ltree, lsent, rtree, rsent, label, ledge, redge = dataset[indices[idx]]
            linput, rinput = Variable(lsent), Variable(rsent)
            target = Variable(map_label_to_target(label))
            ledge_input, redge_input = Variable(ledge), Variable(redge)
            if self.args.cuda:
                linput, rinput = linput.cuda(), rinput.cuda()
                target = target.cuda()
                ledge_input, redge_input = ledge_input.cuda(), redge_input.cuda()

            if self.args.model != 'base':
                output = self.model(ltree, linput, rtree, rinput, ledge_input, redge_input)
            else:
                output = self.model(ltree, linput, rtree, rinput)

            loss = self.criterion(output, target)
            total_loss += loss.data[0]
            loss.backward()
            if idx % self.args.batch_size == 0 and idx > 0:
                self.optimizer.step()
                self.optimizer.zero_grad()

        self.epoch += 1
        return total_loss / len(dataset)

    def test(self, dataset):
        """"""
        self.model.eval()
        total_loss = 0
        predictions = torch.zeros(len(dataset))
        for idx in tqdm(range(len(dataset)), desc='Testing epoch  ' + str(self.epoch) + ''):
            ltree, lsent, rtree, rsent, label, ledge, redge = dataset[idx]
            linput, rinput = Variable(lsent, volatile=True), Variable(rsent, volatile=True)
            target = Variable(map_label_to_target(label), volatile=True)
            ledge_input, redge_input = Variable(ledge, volatile=True), Variable(redge, volatile=True)

            if self.args.cuda:
                linput, rinput = linput.cuda(), rinput.cuda()
                target = target.cuda()
                ledge_input, redge_input = ledge_input.cuda(), redge_input.cuda()

            if self.args.model != 'base':
                output = self.model(ltree, linput, rtree, rinput, ledge_input, redge_input)
            else:
                output = self.model(ltree, linput, rtree, rinput)

            loss = self.criterion(output, target)
            total_loss += loss.data[0]

            _, predict_class = torch.max(output, 1)
            predictions[idx] = predict_class.data.cpu()[0]

        return total_loss / len(dataset), predictions

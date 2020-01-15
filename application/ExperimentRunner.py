import sys

import torch
from torch.utils.tensorboard import SummaryWriter
sys.path.append('framework')
from NetworkClass import Network
import torchvision
from train_utils import ReshapeTransform
import logging

import time

import shutil

logging.basicConfig(level=logging.INFO)

class Experiment:
    def __init__(self):
        self.is_best = True
        self.bestLoss = 999999
        self.tensorboard_summary = SummaryWriter()


    def set_network(self, network):
        self.network = network

    def set_optimizer(self, optimizer):
        self.optimizer = optimizer

    def set_loaders(self, trainLoader, testLoader):
        self.trainLoader = trainLoader
        self.testLoader = testLoader

    def set_loss(self, loss):
        self.loss = loss

    def save_weights(self, state, filename='./checkpoint.pth.tar'):
        torch.save(state, filename)
        if self.is_best:
            shutil.copyfile(filename, './model_best.pth.tar')

    def save_tensorboard_summary(self, loss_dict):
        self.tensorboard_summary.add_scalar('Loss/train', loss_dict['train'], loss_dict['epoch'])
        self.tensorboard_summary.add_scalar('Loss/val', loss_dict['val'], loss_dict['epoch'])
        self.tensorboard_summary.add_scalar('Accuracy/val', loss_dict['acc'], loss_dict['epoch'])
        self.tensorboard_summary.add_scalar('Time/train', loss_dict['traint'], loss_dict['epoch'])
        self.tensorboard_summary.add_scalar('Time/inference', loss_dict['traini'], loss_dict['epoch'])


    
    
    def train_epoch(self, epoch):
        trainLoss = 0.0
        self.network.train()
        start_t = time.time()
        for batch_idx, (data, target) in enumerate(self.trainLoader):
            self.optimizer.zero_grad()
            output = self.network(data)
            loss = self.loss(output, target)
            logging.info("Batch : {} \t Loss: {}".format(batch_idx, loss.item()))
            loss.backward()
            trainLoss += loss.item()
            self.optimizer.step()

        traint = time.time() - start_t
        trainLoss /= len(self.trainLoader.dataset)


        testLoss = 0.0
        correct = 0.0
        self.network.eval()
        start_i = time.time()
        with torch.no_grad():
            for batch_idx, (data, target) in enumerate(self.testLoader):
                output = self.network(data)
                loss = self.loss(output, target)
                testLoss += loss.item()
                pred = output.data.max(1, keepdim=True)[1]
                correct += pred.eq(target.data.view_as(pred)).sum()
                acc = 100. * correct / len(self.testLoader.dataset)
            traini = (time.time() - start_i)/len(self.testLoader.dataset)
            testLoss /= len(self.testLoader.dataset)

        logging.info("VALIDATION: \t Loss: {}, Accuracy : {}".format(testLoss, acc))        
        self.save_tensorboard_summary({'train':trainLoss, 'val': testLoss, 'acc': acc, 'epoch': epoch, 'traint': traint, 'traini': traini})

        self.bestLoss = min(testLoss, self.bestLoss)
        self.is_best = (self.bestLoss == testLoss)

        self.save_weights({
                'epoch': epoch,
                'state_dict': self.network.state_dict(),
                'best_acc1': self.bestLoss,
                'optimizer' : self.optimizer.state_dict(),
                'traint': traint,
                'traini': traini
            })



if __name__ == "__main__":

    batch_size_train = 512
    batch_size_test = 1000
    learning_rate = 0.01
    n_epochs = 100

    experiment = Experiment()
    model_dict = {
        "network":{
            'input_layer': {
                "units": 784,
                
                },
            'hidden_layer': [{
                    "units": 500, 
                    "activation": "relu",
                    "type": "Linear"
                }, 
                {
                    "units": 300, 
                    "activation": "relu",
                    "type": "Linear"

                }],
            'output_layer': {
                "units": 10,
                "activation": "softmax",
                "type": "Linear"
                }
        }
    }

    model = Network(model_dict)
    experiment.set_network(model)
    train_loader = torch.utils.data.DataLoader(
    torchvision.datasets.MNIST('../data/', train=True, download=True,
        transform=torchvision.transforms.Compose([
        torchvision.transforms.ToTensor(),
        torchvision.transforms.Normalize(
            (0.1307,), (0.3081,)), ReshapeTransform((-1,))
        ])),
    batch_size=batch_size_train, shuffle=True)


    test_loader = torch.utils.data.DataLoader(
    torchvision.datasets.MNIST('../data/', train=False, download=True,
        transform=torchvision.transforms.Compose([
        torchvision.transforms.ToTensor(),
        torchvision.transforms.Normalize(
            (0.1307,), (0.3081,)), ReshapeTransform((-1,))
        ])),
    batch_size=batch_size_test, shuffle=True)

    experiment.set_loaders(train_loader, test_loader)
    experiment.set_loss(torch.nn.CrossEntropyLoss())
    experiment.set_optimizer(torch.optim.SGD(model.parameters(), lr=learning_rate))

    for epoch in range(n_epochs):
        experiment.train_epoch(epoch)
        



    

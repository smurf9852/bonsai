from BaseClass import BaseClass
import copy
import torch
import torch.nn as nn
import numpy as np

class Growing(BaseClass):
    def __init__(self):
        pass

    def set_model(self, model):
        self.prev_model = model
        self.new_model = copy.deepcopy(model)
        print("Set Model for Growing: \n")
        self.print_model_structure(self.prev_model)

    def set_optimizer(self, optim):
        self.prev_optimizer = optim
        self.lr = self.prev_optimizer.state_dict()['param_groups'][0]['lr']

    def set_optimizer_model(self, optim, model):
        self.set_model(model)
        self.set_optimizer(optim)

    def set_percentage(self, pruning_perc):
        pass

    def print_model_structure(self, model):
        for (layer, param) in enumerate(model.parameters()):
            print("Layer {} , Parameters: {}".format(layer, param.shape))

    def define_strategy(self):

        #Number of numbers to add per layer, list of integres
        self.number_neurons_per_layer = []

        #Current strategy: add random number of neurons between 0 and 9.
        for p in self.new_model.parameters():
            self.number_neurons_per_layer.append(np.random.randint(10))

    def apply_strategy(self):
        self.define_strategy()

        #Double the list because it passes for both weights and bias
        #list with number of neurons to add per layer

        self.number_neurons_per_layer = [val for val in self.number_neurons_per_layer for _ in (0, 1)]

        #layers
        self.param_list = list(self.new_model.parameters())

        for (i, number_new_neurons) in enumerate(self.number_neurons_per_layer):

            #note: every uneven is weights / every uneven is bias
            #uneven is bias, skip this
            if i % 2 != 0:
                continue

            #dont add neurons to output layer
            if i >= len(self.param_list) - 2 :
                break

            #get layers' weights and biases
            layer_weights_1 = self.param_list[i]
            layer_bias_1 = self.param_list[i+1]
            layer_weights_2 = self.param_list[i+2]

            #get number of neurons
            current_num_nodes_1 = layer_weights_1.shape[1]
            current_num_nodes_2 = layer_weights_2.shape[0]

            #Create new tensors
            add_weights_1 = torch.zeros([number_new_neurons,current_num_nodes_1])
            add_bias_1 = torch.zeros([1,number_new_neurons])
            add_weights_2 = torch.zeros([current_num_nodes_2,number_new_neurons])

            #Randomize
            nn.init.xavier_uniform_(add_weights_1, gain=nn.init.calculate_gain('relu'))
            nn.init.xavier_uniform_(add_bias_1, gain=nn.init.calculate_gain('relu'))
            nn.init.xavier_uniform_(add_weights_2, gain=nn.init.calculate_gain('relu'))

            #merge weights
            new_weights_1 = torch.cat([layer_weights_1,add_weights_1],dim=0) #add bottom row
            new_bias_1 = torch.cat([layer_bias_1,add_bias_1[0]]) #add bottom row
            new_weights_2 = torch.cat([add_weights_2,layer_weights_2],dim=1) #add first column

            #update weights
            layer_weights_1.data = new_weights_1
            layer_weights_2.data = new_weights_2
            layer_bias_1.data = new_bias_1

    #copy pasta from pruning
    def get_model(self):
        print("Get Model after Growing: \n")
        self.print_model_structure(self.new_model)
        return self.new_model

    def get_optimizer(self):
        self.new_optimizer = torch.optim.SGD(self.new_model.parameters(), lr=self.lr)
        self.new_optimizer.load_state_dict(self.prev_optimizer.state_dict())
        return self.new_optimizer

    def get_optimizer_model(self):
        return self.get_optimizer(), self.get_model()

    def grow_model(self, optimizer, model):
        self.set_optimizer_model(optimizer, model)
        self.apply_strategy()
        return self.get_optimizer_model()
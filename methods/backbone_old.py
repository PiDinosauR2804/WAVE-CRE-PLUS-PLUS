# import torch.nn as nn
# import torch
# import numpy as np

# from transformers import BertConfig
# from transformers.models.bert.modeling_bert import BertPreTrainedModel, BertEmbeddings, BertEncoder, BertPooler


# class CustomedBertEmbeddings(BertEmbeddings):
#     def __init__(self, config):
#         super().__init__(config)

#     def custom_freeze_ids(self, non_frozen_ids):
#         self.mask = torch.zeros(self.word_embeddings.weight.shape, dtype=torch.float32).cuda()
#         for _id in non_frozen_ids:
#             self.mask[_id, :] = 1
#         self.word_embeddings.weight.register_hook(self.custom_backward_hook)

#     def custom_backward_hook(self, grad):
#         return grad * self.mask


# class BaseBertEncoder(BertPreTrainedModel):
#     def __init__(self, config):
#         super().__init__(config)
#         self.config = config
#         self.embeddings = CustomedBertEmbeddings(config)
#         self.encoder = BertEncoder(config)
#         self.post_init()

#     def get_input_embeddings(self):
#         return self.embeddings.word_embeddings

#     def set_input_embeddings(self, value):
#         self.embeddings.word_embeddings = value

#     def forward(self, input_ids, prompt_pool=None, x_key=None, prompt_pools=None):
#         out = dict()
#         embeddings_output = self.embeddings(input_ids=input_ids)
#         if prompt_pool is not None:
#             out = prompt_pool(embeddings_output, x_key=x_key)
#             encoder_output = self.encoder(out["prompted_embedding"])
#         elif prompt_pools is not None:
#             outs = []
#             for _, prompt_pool in enumerate(prompt_pools):
#                 embedding_output = torch.index_select(embeddings_output, 0, torch.tensor([_]).cuda())
#                 single_x_key = torch.index_select(x_key, 0, torch.tensor([_]).cuda())
#                 outs.append(prompt_pool(embedding_output, single_x_key))
#             out["prompted_embedding"] = torch.cat([_["prompted_embedding"] for _ in outs])
#             encoder_output = self.encoder(out["prompted_embedding"])
#         else:
#             encoder_output = self.encoder(embeddings_output)
#         sequence_output = encoder_output[0]
#         out["attention_out"] = sequence_output
#         return out


# class BertRelationEncoder(nn.Module):
#     def __init__(self, config):
#         super(BertRelationEncoder, self).__init__()
#         self.encoder = BaseBertEncoder.from_pretrained(config.bert_path)
#         if config.pattern in ["entity_marker"]:
#             self.pattern = config.pattern
#             self.encoder.resize_token_embeddings(config.vocab_size + config.marker_size)
#             self.encoder.embeddings.custom_freeze_ids(list(range(config.vocab_size, config.vocab_size + config.marker_size)))
#         else:
#             raise Exception("Wrong encoding.")

#     def forward(self, input_ids, prompt_pool=None, x_key=None, prompt_pools=None):
#         out = dict()
#         e11 = (input_ids == 30522).nonzero()
#         e21 = (input_ids == 30524).nonzero()

#         out = self.encoder(input_ids, prompt_pool, x_key, prompt_pools)
#         output = []
#         for i in range(e11.shape[0]):
#             if prompt_pool is not None:
#                 additional_length = prompt_pool.length
#             elif prompt_pools is not None:
#                 additional_length = prompt_pools[0].length
#             else:
#                 additional_length = 0

#             instance_output = torch.index_select(out["attention_out"], 0, torch.tensor(i).cuda())
#             instance_output = torch.index_select(instance_output, 1, torch.tensor([e11[i][1], e21[i][1]]).cuda() + additional_length)
#             output.append(instance_output)
#         output = torch.cat(output, dim=0)
#         output = output.view(output.shape[0], -1)
#         out["x_encoded"] = output
#         return out
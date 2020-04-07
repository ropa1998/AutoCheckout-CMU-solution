import json
from collections import namedtuple
from pymongo import MongoClient
import cashier

def _json_object_hook(d): return namedtuple('X', d.keys())(*d.values())
def json2obj(data): return json.load(data, object_hook=_json_object_hook)

groundTruth = None

with open('groundTruthLabelWeightTrigger.json', 'r') as f:
    groundTruth = json2obj(f)

mongoClient = MongoClient('localhost:27017')

db = mongoClient['cps-test-01']
productsDB = db['products']
products = {}

class GTLabeler:
    def __init__(self, planogram):
        gt = GroundTruth()
        for dataset in groundTruth.lists:
            objEvents = []
            for event in dataset.events:
                isProductIncluded = {}
                productList = []
                position = event.observe.position
                gondola = position.gondola - 1
                shelf = position.shelf - 1
                for plate in position.plates:
                    productID = planogram[gondola][shelf][plate-1]
                    if (productID in isProductIncluded) != True:
                        isProductIncluded[productID] = True
                        if (productID in products) != True:
                            product = productsDB.find_one({'product_id.id': productID})
                            if product == None:
                                continue
                                print(product['product_id']['id'])
                            objProduct = Product(
                                product['product_id']['id'],
                                product['product_id']['barcode_type'],
                                product['metadata']['name'],
                                product['metadata']['thumbnail'],
                                product['metadata']['price'],
                                product['metadata']['weight']
                            )
                            # print(objProduct.toJSON())
                            products[productID] = objProduct
                        productList.append(products[productID])
                objPosition = Position(position.gondola, position.shelf, position.plates)
                objObservation = Observation(productList, event.observe.time, objPosition)
                objEvent = Event(event.eventID, event.putback, objObservation)
                objEvents.append(objEvent)
            objDataset = Dataset(dataset.dataset, objEvents)
            gt.lists.append(objDataset)
        
        print(len(gt.lists))
        dump = open("./gt.json", 'w')
        dump.write(gt.toJSON())

class Serializable:
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=2)

class GroundTruth(Serializable):
    def __init__(self):
        self.lists = []

class Position(Serializable):
    def __init__(self, gondola, shelf, plates):
        self.gondola = gondola
        self.shelf = shelf
        self.plates = plates

class Product(Serializable):
    def __init__(self, id, barcodeType, name, thumbnail, price, weight):
        self.id = id
        self.barcodeType = barcodeType
        self.name = name
        self.thumbnail = thumbnail
        self.price = price
        self.weight = weight

class Observation(Serializable):
    def __init__(self, products, time, position):
        self.products = products
        self.time = time
        self.position = position

class Event(Serializable):
    def __init__(self, eventID, putback, observation):
        self.eventID = eventID
        self.putback = putback
        self.observation = observation

class Dataset(Serializable):
    def __init__(self, dataset, events):
        self.dataset = dataset
        self.events = events


# {
#   "lists": [
#     {
#       "dataset": "2019-11-07_02-35",
#       "events": [
#         {
#           "eventID": 1,
#           "putback": 0,
#           "observe": {
#             "product": "",
#             "time": "2019-11-07_02-35-28",
#             "position": {
#               "gondola": 2,
#               "shelf": 6,
#               "plates": [
#                 8,
#                 9
#               ]
#             }
#           }
#         },
#         {
#           "eventID": 1,
#           "putback": 0,
#           "observe": {
#             "product": "",
#             "time": "2019-11-07_02-35-28",
#             "position": {
#               "gondola": 2,
#               "shelf": 6,
#               "plates": [
#                 8,
#                 9
#               ]
#             }
#           }
#         }
#       ]
#     }
#   ]
# }

# class GroundTruth(Serializable):

if __name__ == '__main__':
    """Main function"""
    gtLabeler = GTLabeler(cashier.planogram)
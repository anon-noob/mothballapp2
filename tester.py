import datetime
import random

my_list = ['apple', 'banana', 'cherry']

# def get_deterministic_choice(seed):
#     random.seed(seed)
#     return random.choice(my_list)

random.seed(datetime.datetime.now(datetime.timezone.utc).toordinal())

print(random.choice(my_list))
random.seed(datetime.datetime.now(datetime.timezone.utc).toordinal())
print(random.choice(my_list))
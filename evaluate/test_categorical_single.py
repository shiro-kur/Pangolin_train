import sys
from model import *
from utils import *

if sys.argv[1] == "spliceai":
    spliceai = True
else:
    tissue = int(sys.argv[1])
    spliceai = False
    assert tissue in [0,2,4,6]

if spliceai:
    from tensorflow.keras.models import load_model
    import tensorflow as tf
    # https://stackoverflow.com/questions/43147983/could-not-create-cudnn-handle-cudnn-status-internal-error
    physical_devices = tf.config.experimental.list_physical_devices('GPU')
    assert len(physical_devices) > 0, "Not enough GPU hardware devices available"
    config = tf.config.experimental.set_memory_growth(physical_devices[0], True)
    SpliceAI = []
    for i in range(1,6):
        SpliceAI.append(load_model('../SpliceAI/spliceai/models/spliceai' + str(i) + '.h5'))
else:
    prefix = sys.argv[3]
    weights = [prefix+'/'+f for f in sys.argv[4].split(',')]
    #weights = ["final.1.%s.3"%tissue,"final.2.%s.3"%tissue,"final.3.%s.3"%tissue,"final.4.%s.3"%tissue,"final.5.%s.3"%tissue]
    #weights = ["Pangolin/pangolin/models/"+weight for weight in weights]

    models = []
    for i in range(0,len(weights)):
        model = Pangolin(L, W, AR)
        model.cuda()
        model.load_state_dict(torch.load(weights[i]), strict=True)
        model.eval()
        models.append(model)

ds = H5Dataset(sys.argv[2])
dl = data.DataLoader(ds, batch_size=1)

spliceai_outputs = np.empty([len(dl),3,5000], dtype=np.float16)
all_targets = np.empty([len(dl),12,5000], dtype=np.float16)
all_outputs = np.empty([len(dl),12,5000], dtype=np.float16) 

for batch_idx, (inputs, targets) in enumerate(dl):
    if batch_idx % 1000 == 0:
        print(batch_idx, flush=True)

    all_targets[batch_idx:batch_idx+1,:,:] = targets.numpy()

    if spliceai:
        for model in SpliceAI:
            outputs = model.predict(inputs.permute(0,2,1).numpy(), batch_size=1)
            spliceai_outputs[batch_idx:batch_idx+1,:,:] += np.transpose(outputs,(0,2,1))
    else:
        inputs = inputs.cuda()
        all_targets[batch_idx:batch_idx+1,:,:] = targets.numpy()
        for model in models:
            all_outputs[batch_idx:batch_idx+1,:,:] += model(inputs).cpu().detach().numpy()

## 0,1|2|3,4|5|6,7|8|9,10|11 (split before the indicated idx)
all_targets = np.split(all_targets, [2,3,5,6,8,9,11], axis=1)
np.set_printoptions(threshold=sys.maxsize)
print(all_targets[0])
if spliceai:
    print_metrics(all_targets[0], spliceai_outputs, spliceai=True)
    print_metrics(all_targets[2], spliceai_outputs, spliceai=True)
    print_metrics(all_targets[4], spliceai_outputs, spliceai=True)
    print_metrics(all_targets[6], spliceai_outputs, spliceai=True)
else:
    all_outputs = np.split(all_outputs, [2,3,5,6,8,9,11], axis=1)
    print_metrics(all_targets[tissue], all_outputs[tissue])






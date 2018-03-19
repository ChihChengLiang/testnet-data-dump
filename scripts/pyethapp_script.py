"""
git clone https://github.com/karlfloersch/docker-pyeth-dev/
cd docker-pyeth-dev
docker run -it --rm \
    -v $PWD/bootstrap/data/config:/root/.config/pyethapp \
    -p 30303:30303 \
    -p 30303:30303/udp \
    -p 8545:8545 \
    --name pyethapp \
    ethresearch/pyethapp-research:beta-testnet \
    pyethapp  run
# Enter console with Ctrl-C
"""


from ethereum.tools import tester
from ethereum.hybrid_casper import casper_utils
from ethereum.utils import encode_hex
casper = tester.ABIContract(tester.State(eth.chain.state), casper_utils.casper_abi, eth.chain.config['CASPER_ADDRESS'])

def validators(casper, deposit_scale_factor):
    validator_num = casper.get_nextValidatorIndex()
    validators = []
    for validator_index in range(1, validator_num):
        v = {}
        v["addr"] = casper.get_validators__addr(validator_index)
        v["start_dynasty"] = casper.get_validators__start_dynasty(validator_index)
        v["end_dynasty"] = casper.get_validators__end_dynasty(validator_index)
        v["deposit"] = casper.get_validators__deposit(validator_index)/10**18 * deposit_scale_factor
        validators.append(v)
    return validators

def votes_and_deposits(casper, ce, ese, deposit_scale_factor):
    cur_deposits = casper.get_total_curdyn_deposits()
    prev_deposits = casper.get_total_prevdyn_deposits()

    cur_votes = casper.get_votes__cur_dyn_votes(ce, ese) * deposit_scale_factor
    prev_votes = casper.get_votes__prev_dyn_votes(ce, ese) * deposit_scale_factor
    cur_vote_pct = cur_votes * 100 / cur_deposits if cur_deposits else 0
    prev_vote_pct = prev_votes * 100 / prev_deposits if prev_deposits else 0
    last_nonvoter_rescale, last_voter_rescale = casper.get_last_nonvoter_rescale(), casper.get_last_voter_rescale()
    return {
        "cur_deposits":cur_deposits / 10**18,
        "prev_deposits":prev_deposits / 10**18,
        "cur_votes":cur_votes / 10**18,
        "prev_votes":prev_votes / 10**18,
        "cur_vote_pct":cur_vote_pct,
        "prev_vote_pct":prev_vote_pct,
        "last_nonvoter_rescale":last_nonvoter_rescale,
        "last_voter_rescale":last_voter_rescale
    }

def epoch_info(epoch):
    height = epoch *50 + 49
    block = eth.chain.get_block_by_number(height)
    blockhash = block.hash
    ts = block.timestamp
    temp_state = eth.chain.mk_poststate_of_blockhash(blockhash)
    casper = tester.ABIContract(tester.State(temp_state), casper_utils.casper_abi, eth.chain.config['CASPER_ADDRESS'])

    ce, ese = casper.get_current_epoch(), casper.get_expected_source_epoch()
    deposit_scale_factor = casper.get_deposit_scale_factor(ce)
    storage = len(tester.State(temp_state).state.account_to_dict(eth.chain.config['CASPER_ADDRESS'])["storage"])

    info = {}
    info["number"] = height
    info["blockhash"] = encode_hex(blockhash)
    info["timestamp"] = ts
    info["difficulty"] = block.difficulty
    info["current_epoch"] = ce
    info["validators"] = validators(casper, deposit_scale_factor)
    info["lje"] = casper.get_last_justified_epoch()
    info["lfe"] = casper.get_last_finalized_epoch()
    info["votes"] = votes_and_deposits(casper, ce, ese, deposit_scale_factor)
    info["deposit_scale_factor"] = deposit_scale_factor
    info["storage"] = storage
    return info

for epoch in range(5):
    info = epoch_info(epoch)
    print(info)

latest_epoch = eth.latest.number // 50

import json
with open("/root/.config/pyethapp/epoch.json", "w") as f:
    for epoch in range(latest_epoch):
        info = epoch_info(epoch)
        print(info)
        f.write(json.dumps(info))
        f.write('\n')

# coding: utf-8

import pytest

from Utils import is_a_valid_index_url
import pgpy
import json

def test_indexjson_url_checker():
	assert is_a_valid_index_url("https://onlinemektep.net/upload/online_mektep/lesson/72e41ed08452870a27fb545006e27781/index.json") # Should be True
	assert is_a_valid_index_url("https://onlinemektep.net/upload/online_mektep/lesson/18772e600545bf72a07825480de14e27/index.json") # Should be True
	assert not is_a_valid_index_url("https://onlinemektep.net/upload/online_mektep/lesson/THIS_SHOULD_BE_FALSE!/index.json")        # Should be False
	assert not is_a_valid_index_url("https://onlinemektep.net/upload/online_mektep/lesson/THIS_SHOULD_BE_FALSE!/index.json.")       # Should be False
    
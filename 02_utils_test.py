# coding: utf-8

import Utils as utils
import shutil

def test_indexjson_url_checker():
	assert utils.is_a_valid_index_url("https://onlinemektep.net/upload/online_mektep/lesson/72e41ed08452870a27fb545006e27781/index.json") # Should be True
	assert utils.is_a_valid_index_url("https://onlinemektep.net/upload/online_mektep/lesson/18772e600545bf72a07825480de14e27/index.json") # Should be True
	assert not utils.is_a_valid_index_url("https://onlinemektep.net/upload/online_mektep/lesson/THIS_SHOULD_BE_FALSE!/index.json")        # Should be False
	assert not utils.is_a_valid_index_url("https://onlinemektep.net/upload/online_mektep/lesson/THIS_SHOULD_BE_FALSE!/index.json.")       # Should be False

def test_save_db():
	utils.save_user_info({
		"Boolean": True
	}, 1, "Temp-Testing/")

	utils.save_user_info({
		"Boolean": True
	}, -1, "Temp-Testing/")

	assert True

def test_load_db():
	data = utils.load_user_info(-1, "Temp-Testing/")

	assert data["Boolean"]

	shutil.rmtree(
		"Temp-Testing/"
	)
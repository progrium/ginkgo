import unittest

from ginkgo import util

class GlobalContextTest(unittest.TestCase):
    singleton_a = None
    singleton_b = None

    def setUp(self):
        GlobalContextTest.singleton_a = object()
        GlobalContextTest.singleton_b = object()


    def test_push_pop_of_singleton(self):
        class TestContext(util.GlobalContext):
            singleton_attr = (GlobalContextTest, 'singleton_a')
        def _singleton_id():
            return id(GlobalContextTest.singleton_a)
        original_id = _singleton_id()
        new_object = object()
        TestContext._push_context(new_object)
        assert not _singleton_id() == original_id
        assert _singleton_id() == id(new_object)
        TestContext._pop_context()
        assert not _singleton_id() == id(new_object)
        assert _singleton_id() == original_id

    def test_nested_push_pop_of_two_singletons(self):
        class TestContext(util.GlobalContext):
            singleton_attr = (GlobalContextTest, 'singleton_a')
        def _singleton_id():
            return id(GlobalContextTest.singleton_a)
        original_id = _singleton_id()
        first_object = object()
        second_object = object()
        assert _singleton_id() == original_id
        TestContext._push_context(first_object)
        assert _singleton_id() == id(first_object)
        TestContext._push_context(second_object)
        assert _singleton_id() == id(second_object)
        TestContext._pop_context()
        assert _singleton_id() == id(first_object)
        TestContext._pop_context()
        assert _singleton_id() == original_id

    def test_multiple_global_contexts(self):
        class FirstContext(util.GlobalContext):
            singleton_attr = (GlobalContextTest, 'singleton_a')
        class SecondContext(util.GlobalContext):
            singleton_attr = (GlobalContextTest, 'singleton_b')
        def _first_singleton_id():
            return id(GlobalContextTest.singleton_a)
        def _second_singleton_id():
            return id(GlobalContextTest.singleton_b)
        first_original_id = _first_singleton_id()
        second_original_id = _second_singleton_id()
        assert not first_original_id == second_original_id
        first_object = object()
        second_object = object()
        FirstContext._push_context(first_object)
        assert _first_singleton_id() == id(first_object)
        assert not _second_singleton_id() == id(first_object)
        SecondContext._push_context(second_object)
        assert _second_singleton_id() == id(second_object)
        assert not _first_singleton_id() == id(second_object)
        assert _first_singleton_id() == id(first_object)
        FirstContext._pop_context()
        assert _first_singleton_id() == first_original_id
        SecondContext._pop_context()
        assert _second_singleton_id() == second_original_id

    def test_context_manager(self):
        class TestContext(util.GlobalContext): pass
        TestContext.singleton_attr = (GlobalContextTest, 'singleton_a')
        GlobalContextTest.singleton_a = TestContext()
        original_id = id(GlobalContextTest.singleton_a)
        new_context = TestContext()
        with new_context:
            assert not original_id == id(GlobalContextTest.singleton_a)
            assert id(new_context) == id(GlobalContextTest.singleton_a)
        assert original_id == id(GlobalContextTest.singleton_a)

    def test_nested_context_managers(self):
        class TestContext(util.GlobalContext): pass
        TestContext.singleton_attr = (GlobalContextTest, 'singleton_a')
        GlobalContextTest.singleton_a = TestContext()
        original_id = id(GlobalContextTest.singleton_a)
        first_context = TestContext()
        second_context = TestContext()
        with first_context:
            assert id(first_context) == id(GlobalContextTest.singleton_a)
            with second_context:
                assert id(second_context) == id(GlobalContextTest.singleton_a)
            assert id(first_context) == id(GlobalContextTest.singleton_a)
        assert original_id == id(GlobalContextTest.singleton_a)

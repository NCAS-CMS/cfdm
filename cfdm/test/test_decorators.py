import copy
import datetime
import unittest

import cfdm


class dummyClass:
    '''Dummy class acting as container to test methods as proper instance
       methods, mirroring their context in the codebase.
    '''
    def __init__(self):
        self._list = [1]

    def copy(self):
        return copy.deepcopy(self)  # note a shallow copy is not sufficient

    def func(self, inplace):
        '''Dummy function to do something trivial to a mutable object,
           potentially in-place as toggled by an in-place flag.
        '''
        if inplace:
            d = self
        else:
            d = self.copy()

        d._list.append(2)

        if inplace:
            d = None
        return d

    @cfdm.decorators._inplace_enabled
    def decorated_func(self, inplace):
        '''Dummy function equivalent to 'func' but a decorator manages the
           logic to specify and conduct in-place operation.
        '''
        d = cfdm.decorators._inplace_enabled_define_and_cleanup(self)
        d._list.append(2)
        return d

# --- End: class


class DecoratorsTest(unittest.TestCase):
    def setUp(self):
        self.test_only = []

    def test_inplace_enabled(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        # Note we must initiate separate classes as a list is mutable:
        test_class_1 = dummyClass()
        test_class_2 = dummyClass()

        # Test when not in-place
        res_1 = test_class_1.func(inplace=False)
        res_2 = test_class_2.decorated_func(inplace=False)
        self.assertEqual(test_class_1._list, test_class_2._list)
        self.assertEqual(test_class_2._list, [1])  # as original list untouched
        self.assertEqual(res_1._list, res_2._list)
        self.assertEqual(res_2._list, [1, 2])  # as return d copy, not original

        # Test when in-place
        res_3 = test_class_1.func(inplace=True)
        res_4 = test_class_2.decorated_func(inplace=True)

        self.assertEqual(test_class_1._list, test_class_2._list)
        # As do the operation in-place on the original (class) list object:
        self.assertEqual(test_class_2._list, [1, 2])
        self.assertEqual(res_3, res_4)
        self.assertEqual(res_4, None)  # as return None if inplace=True

# --- End: class


if __name__ == '__main__':
    print('Run date:', datetime.datetime.now())
    print(cfdm.environment(display=False))
    print('')
    unittest.main(verbosity=2)

from itertools import islice

class PagedResource:
    """List adapter for paged resources. Returns sliceable lazy loaded object."""
    pages = {}
    page_size = 20
    page_count = None

    def __init__(self, api, params=None):
        self.api = api
        self.params = params or {}

    def load_page(self, n):
        raise NotImplementedError("You must implement load_page method.")

    def ensure_page_count(self):
        if self.page_count is None:
            #load any page to get page count from headers
            self.get_page(0)

    def get_page(self, n):
        if self.page_count and n >= self.page_count:
            raise IndexError('index out of range')
        if n in self.pages:
            return self.pages[n]
        page = self.load_page(n)
        if page:
            self.pages[n] = page
            return page
        raise IndexError('index out of range')

    def __len__(self):
        self.ensure_page_count()
        return self.page_size * (self.page_count-1) + len(self.get_page(self.page_count-1))

    def __getitem__(self, key):
        if isinstance(key, int):
            if key < 0:
                key = len(self) + key
                if key < 0:
                    raise IndexError('index out of range')
            page_n, idx = divmod(key, self.page_size)
            return self.get_page(page_n)[idx]
        elif isinstance(key, slice):
            #TODO support negative step
            return islice(self, *key.indices(len(self)))
        else:
            raise TypeError('list indices must be integers')

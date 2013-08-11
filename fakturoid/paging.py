class PagedResource:
    """List adapter for paged resources."""
    pages = {}
    page_size = 10
    known_page_out_of_bound = 1 << 31  # number larger than any real page

    def __init__(self, api, params=None):
        self.api = api
        self.params = params or {}

    def load_page(self, n):
        raise NotImplementedError("You must implement load_page method.")

    def get_page(self, n):
        if n >= self.known_page_out_of_bound:
            raise IndexError('index of ouf range')
        if n in self.pages:
            return self.pages[n]
        page = self.load_page(n)
        if page:
            if len(page) < self.page_size:
                self.known_page_out_of_bound = n + 1
            self.pages[n] = page
            return page
        self.known_page_out_of_bound = min(self.known_page_out_of_bound, n)
        raise IndexError('index of ouf range')

    def __getitem__(self, key):
        if isinstance(key, int):
            if key < 0:
                raise ValueError("negative index is not allowed")
            page_n, idx = divmod(key, self.page_size)
            return self.get_page(page_n)[idx]
        elif isinstance(key, slice):
            if key.start and key.start < 0:
                raise ValueError("negative start indice is not allowed")
            invoices = []
            i = key.start or 0
            if key.stop and key.stop >= 0:
                stop = key.stop
            else:
                stop = 1 << 31
            while i < stop:
                try:
                    invoices.append(self[i])
                    i += 1
                except IndexError:
                    break
            stop = key.stop if key.stop and key.stop < 0 else None
            return invoices[:stop:key.step]
        else:
            raise TypeError('list indices must be integers')

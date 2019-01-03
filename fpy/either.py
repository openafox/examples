class Either:
 
    def __init__(self, left, right):
        self.right = right
        self.left = left
        
    
    @staticmethod
    def Try(a):
        try:
            return Either.Right(a)
        except Exception as e:
            return Either.Left(e)
    
    @staticmethod
    def Right(a):
        """ Runs a """
        return Either(None, a())
    
    @staticmethod
    def Left(e):
        """Returns error, None"""
        return Either(e, None)

    def filter(self, f): # (a: A, f: A => Bool) => Either(A)
        if self.left:
            return self
        else:
            try:
                f(self.right) # Must throw appropriate error
                return self
            except Exception as e:
                return Either.Left(e)
            
    def map(self,f): # (a: A, f: A => B) => Either(B)
        if self.left:
            return self
        else:
            return Either.Try(lambda: f(self.right))

       
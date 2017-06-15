# ck4, add some simple tests for this class
class Version(object, ):
    class InvalidVersionFormat(Exception): pass

    def __init__(self, version_str):
        self.version_str = version_str
        try:
            self.version_components = []
            for component in version_str.split('.'):
                # verify no leading 0s are present, as they will be 'normalized' by pip install, causing untold future problems
                if component == str(int(component)):
                    self.version_components.append(int(component))
                else:
                    raise self.InvalidVersionFormat('Versions must be of the form: n0.n1.n2 ... (nX being a non-negative integer, no leading 0s)')
        except ValueError as e:
            raise self.InvalidVersionFormat('Versions must be of the form: n0.n1.n2 ... (nX being a non-negative integer, no leading 0s)')

        self.length = len(self.version_components)
        if not self.length > 0:
            raise self.InvalidVersionFormat('Versions must be of the form: n0.n1.n2 ... (nX being a non-negative integer), no leading 0s')

    def __cmp__(self, other_version):
        """
        Left-to-right comparison of versions. Versions must be of the same length.
        :param other_version: another Version object
        :return: negative int, 0, positive int corresponding to v < other, v == other, v > other
        """
        if not isinstance(other_version, Version):
            other_version = Version(other_version)
        if self.length != other_version.length:
            raise Exception('Versions of differing lengths cannot be compared: %s (%d) vs %s (%d)' %
                            (self.version_str, self.length, other_version.version_str, other_version.length))
        difference = 0
        digit = 0
        while difference == 0 and digit < self.length:
            difference = self.version_components[digit] - other_version.version_components[digit]
            digit += 1
        return difference

    def __str__(self):
        return self.version_str

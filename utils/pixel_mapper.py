import numpy as np
import pyproj


class PixelMapper:
    metadata = {}
    munu = []

    def __init__(self, metadata):
        self.metadata = metadata
        self.calc_munu(self.metadata)

    def get_raster2geo(self, rc):
        """
        Convert row and column to geographic coordinates
        """
        va = self.metadata['va']
        vc = self.metadata['vc']
        vs = self.metadata['vs']
        eta_corners = self.metadata['eta_corners']
        ecef = self.metadata['ecef']
        lla = self.metadata['lla']
        kappa = (rc[1]-1/2)/self.metadata['samples']
        rho = (rc[0]-1/2)/self.metadata['lines']
        mu = self.munu[0]
        nu = self.munu[1]
        y = kappa*(va + mu*(va-vs)) + rho*(vc + nu*(vc-vs)) # IN MATLAB line 105 differ
        B = np.array([va, vc, vs-y]).T
        ags = np.linalg.solve(B, y.T)
        al = ags[0]
        gm = ags[1]
        eta = eta_corners[0, :] + al*va + gm*vc
        lon, lat, alt = pyproj.transform(ecef, lla, eta[0], eta[1], eta[2], radians=False)
        return [lat, lon]

    def get_geo2raster(self, llh):
        """
        Convert geographic coordinates to row and column
        If row and column cannot be determined returns []
        """
        mu = self.munu[0]
        nu = self.munu[1]
        va = self.metadata['va']
        vc = self.metadata['vc']
        vs = self.metadata['vs']
        ll_corners = self.metadata['ll_corners']
        ecef = self.metadata['ecef']
        lla = self.metadata['lla']
        samples = self.metadata['samples']
        lines = self.metadata['lines']
        if len(llh) == 2:
            llh.append(0)
        x1, y1, z1 = pyproj.transform(lla, ecef, llh[1], llh[0], llh[2], radians=False)
        x2, y2, z2 = pyproj.transform(lla, ecef, ll_corners[0, 1], ll_corners[0, 0], ll_corners[0, 2], radians=False)
        x = np.array([x1-x2, y1-y2, z1-z2])
        v = np.cross(vc, va)
        xh = np.divide(np.dot(v.T, x), np.linalg.norm(v))
        x1, y1, z1 = pyproj.transform(lla, ecef, llh[1], llh[0], -xh, radians=False)
        x = np.array([x1-x2, y1-y2, z1-z2])
        A = np.array([(1+mu)*va-mu*vs, (1+nu)*vc-nu*vs, x-vs]).T
        z = np.linalg.solve(A, x.T)
        kappa = round(z[0], 4)
        rho = round(z[1], 4)
        if kappa < 0 or kappa > 1 or rho < 0 or rho > 1:
            return []
        else:
            l1 = min([max([1, round(rho*lines + 0.5)]), lines])
            l2 = min([max([1, round(kappa*samples + 0.5)]), samples])
            return [int(l1), int(l2)]

    def calc_munu(self, metadata):
        """
        Calc and return mu and nu (nadir parameters)
        """
        va = metadata['va']
        vb = metadata['vb']
        vc = metadata['vc']
        vs = metadata['vs']
        b = np.array([vb - (va + vc)])
        A = np.array([va - vs, vc - vs, vb - vs])
        self.munu = np.linalg.solve(A.T, b.T)  # mu = mns[0], nu = mns[1]


import numpy as np
import h5py 
import matplotlib as mt
import matplotlib.pyplot as plt
import animation as an

def main():
    f           = h5py.File("./demo.hdf5","r",swmr=True)
    dset        = f["/sequence"]
    print(dset.shape)
    it,dy,dx    = dset.shape

    ani = an.anim.anim( [dset],
                        ["{}".format(i) for i in range(it)],
                        num_axis=1,
                        max_count=it)
    ani.set_FPS(10)
    im          = ani.ax.imshow(dset[0,:,:],cmap="gray")
    ani.ax.axis(False)

    def update(ax,li,data,title,num):
        li[0].set_array(data[0][num,:,:])
        ax.draw_artist(li[0])
        ax.set_title(title)

    ani.animate([im],update)

    plt.show()
    f.close()

if __name__ == "__main__":
    main()

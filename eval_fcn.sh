python eval_fcn.py --name cityscapes_from_GTA5 --dataset_mode cityscapes \
                --phase test \
                --label_nc 19 --no_instance --no_flip \
                --dataroot /data/yzhang/cityscapes \
                --use_vae \
                --vgg_norm \
                --model_path /data/yingda/Domain-Adaptation/checkpoints/fcn8s/cityscapes_c19-iter100000.pth \
                --gpu_ids 0
#--model_path checkpoints/fcn8s/cityscapes_from_GTA5-iter100000.pth \

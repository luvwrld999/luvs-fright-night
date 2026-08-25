#ifndef LFN_ENTITIES_H
#define LFN_ENTITIES_H

#include "bn_camera_ptr.h"
#include "bn_fixed_point.h"
#include "bn_optional.h"
#include "bn_sprite_ptr.h"
#include "bn_vector.h"

#include "lfn_level.h"
#include "lfn_luv.h"

namespace lfn
{
    enum class ent_kind : uint8_t
    {
        none, imp, cherub, gnasher, wraith, bat, jet,
        soul, pu_flame, pu_soul, pu_dash, pu_wings, one_up,
        checkpoint, exit_gate, flame, ember, warp,
    };

    struct entity
    {
        bn::fixed_point pos;
        bn::fixed_point vel;
        bn::fixed_point home;
        bn::optional<bn::sprite_ptr> sprite;
        int timer = 0;
        int life = 0;
        ent_kind kind = ent_kind::none;
        uint8_t frame = 0;
        bool alive = false;
        bool awake = false;
        bool facing_right = false;
        bool hidden = false;     // sealed inside a breakable block
    };

    /** What the world did to, or for, the player this frame. */
    struct world_events
    {
        int souls = 0;
        int lives = 0;
        bool powered_up = false;
        bool stomped = false;
        bool enemy_killed = false;
        bool checkpoint = false;
        bool exited = false;
        bool warped = false;
        bool hurt = false;
    };

    class entities
    {
    public:
        void load(const level_data& data, bn::camera_ptr& camera);
        void clear();

        world_events update(luv& player, level& lv);

        void spawn_flame(bn::fixed x, bn::fixed y, bool right);

        /** A hostile shot, used by the wraiths and by every boss. */
        void spawn_shot(bn::fixed x, bn::fixed y, bn::fixed vx, bn::fixed vy,
                        int life = 200);

        /** Spawn an enemy mid-fight (bosses that call for help). */
        void spawn_enemy(ent_kind kind, bn::fixed x, bn::fixed y);

        /** How many enemies are currently alive, for bosses that call for help. */
        [[nodiscard]] int live_enemies() const;

        /**
         * Consume a soul flame overlapping this box, if there is one. Bosses
         * live outside the pool, so this is how they take fire.
         */
        [[nodiscard]] bool flame_hits(bn::fixed x, bn::fixed y, int half);

        /** Let out whatever was sealed in the block at this cell. */
        void reveal(int col, int row);

        [[nodiscard]] bn::fixed_point checkpoint_position() const { return _checkpoint; }
        [[nodiscard]] bool has_checkpoint() const { return _has_checkpoint; }

    private:
        static constexpr int capacity = 48;

        bn::vector<entity, capacity> _pool;
        bn::optional<bn::camera_ptr> _camera;
        bn::fixed_point _checkpoint;
        bool _has_checkpoint = false;
        bn::fixed _cam_x = 0;

        entity* _free_slot();
        void _wake(entity& e);
        void _sleep(entity& e);
        void _behave(entity& e, luv& player, level& lv, world_events& ev);
        void _collide(entity& e, luv& player, world_events& ev);
        bool _burn(entity& target);
        void _draw(entity& e);
    };
}

#endif
